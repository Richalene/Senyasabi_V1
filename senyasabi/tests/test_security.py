"""Section 13 - Security SEC-001 .. SEC-008."""
import asyncio
import base64
import json
import re
import sys
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import APP_ROOT, OfflineAuthCase, qt_app  # noqa: E402

from sqlalchemy import text  # noqa: E402

try:
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    from jose import jwt
    from backend import security
    HAVE_API = True
except ImportError:
    HAVE_API = False

GOOD_PW = "CorrectPass123"


class LoginBehaviourTests(OfflineAuthCase):
    def test_sec_001_invalid_login_gives_generic_error_and_no_session(self):
        self.auth.register_user("mary", "mary@example.com", GOOD_PW, "Mary")
        with self.assertRaises(self.auth.AuthError) as ctx:
            self.auth.authenticate_user("mary", "wrong-password")
        self.assertEqual(str(ctx.exception), self.auth.INVALID)
        self.assertIsNone(self.auth.get_current_user())
        self.assertIsNone(self.auth.get_access_token())

    @unittest.skipUnless(HAVE_API, "FastAPI stack unavailable")
    def test_sec_001_api_login_does_not_reveal_which_part_was_wrong(self):
        from backend.api import auth as api_auth
        body = api_auth.LoginBody(identifier="ghost", password="whatever123")
        with patch.object(api_auth, "_email_for_username", return_value=None):
            with self.assertRaises(HTTPException) as unknown:
                api_auth.login(body)
        bad = Mock = None  # noqa: F841
        from unittest.mock import Mock
        response = Mock(status_code=400, text="")
        response.json.return_value = {"error_code": "invalid_credentials"}
        with patch.object(api_auth, "_email_for_username", return_value="ghost@example.com"), \
                patch.object(api_auth, "_gotrue", return_value=response):
            with self.assertRaises(HTTPException) as wrong:
                api_auth.login(body)
        self.assertEqual((unknown.exception.status_code, unknown.exception.detail),
                         (wrong.exception.status_code, wrong.exception.detail))

    def test_sec_003_passwords_are_hashed_with_argon2id(self):
        self.auth.register_user("mary", "mary@example.com", GOOD_PW, "Mary")
        with self.db.scope() as s:
            verifier = s.execute(text("SELECT password_verifier FROM offline_auth")).scalar()
            user_columns = [r[1] for r in s.execute(text("PRAGMA table_info(users)"))]
        self.assertTrue(verifier.startswith("$argon2id$"))
        self.assertNotIn(GOOD_PW, verifier)
        self.assertFalse([c for c in user_columns if "pass" in c.lower()])

    def test_sec_004_logout_terminates_session(self):
        self.auth.register_user("mary", "mary@example.com", GOOD_PW, "Mary")
        user = self.auth.authenticate_user("mary", GOOD_PW)
        self.auth._session = {"access_token": "t", "refresh_token": "r", "expires_at": time.time() + 3600}
        self.auth._pending_tokens["x"] = {"access_token": "p"}
        self.auth.logout_user()
        self.assertIsNone(self.auth.get_current_user())
        self.assertIsNone(self.auth._session)
        self.assertEqual(self.auth._pending_tokens, {})
        self.assertIsNone(self.auth.get_access_token())
        self.store.return_value.delete_refresh_token.assert_called_once_with(str(user["user_id"]))

    def test_sec_005_sql_injection_strings_are_inert(self):
        payloads = ["admin'; DROP TABLE users;--", "' OR '1'='1", '" OR ""="', "1; DELETE FROM offline_auth"]
        self.auth.register_user("mary", "mary@example.com", GOOD_PW, "Mary")
        for payload in payloads:
            with self.assertRaises(self.auth.AuthError):
                self.auth.authenticate_user(payload, "x")
            with self.assertRaises(self.auth.AuthError):
                self.auth.register_user(payload, "p@example.com", GOOD_PW)
        self.auth.register_user("inject_user", "o'brien';--@example.com", GOOD_PW)   # stored literally
        self.assertIsNotNone(self.auth._repository.find_by_identifier("o'brien';--@example.com"))
        with self.db.scope() as s:
            self.assertEqual(s.execute(text("SELECT count(*) FROM users")).scalar(), 2)
            self.assertEqual(s.execute(text("SELECT count(*) FROM offline_auth")).scalar(), 2)

    def test_sec_007_lockout_after_repeated_failures(self):
        from backend.config import OFFLINE_AUTH_MAX_FAILED_ATTEMPTS as LIMIT
        self.auth.register_user("mary", "mary@example.com", GOOD_PW, "Mary")
        last = ""
        for _ in range(LIMIT):
            with self.assertRaises(self.auth.AuthError) as ctx:
                self.auth.authenticate_offline("mary", "wrong", establish_session=False)
            last = str(ctx.exception)
        self.assertIn("Locked", last)
        with self.assertRaises(self.auth.AuthError) as ctx:                       # even the right password
            self.auth.authenticate_offline("mary", GOOD_PW, establish_session=False)
        self.assertIn("Too many", str(ctx.exception))
        self.assertIsNone(self.auth.get_current_user())


@unittest.skipUnless(HAVE_API, "FastAPI / python-jose stack unavailable")
class TokenAndAuthorizationTests(unittest.TestCase):
    SECRET = "unit-test-secret-that-is-long-enough-32-bytes"

    def setUp(self):
        for name, value in (("ISSUER", "https://example.supabase.co/auth/v1"),
                            ("SUPABASE_JWT_SECRET", self.SECRET)):
            p = patch.object(security, name, value)
            p.start()
            self.addCleanup(p.stop)

    def _token(self, secret=None, **override):
        claims = {"sub": str(uuid.uuid4()), "aud": "authenticated", "iss": security.ISSUER,
                  "exp": int(time.time()) + 300}
        claims.update(override)
        return jwt.encode(claims, secret or self.SECRET, algorithm="HS256"), claims

    def _validate(self, token):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return asyncio.run(security.validate_supabase_token(creds))

    def _assert_rejected(self, token):
        with self.assertRaises(HTTPException) as ctx:
            self._validate(token)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_sec_002_valid_token_identifies_only_its_owner(self):
        token, claims = self._token()
        self.assertEqual(self._validate(token)["user_id"], claims["sub"])

    def test_sec_002_forged_expired_and_unsigned_tokens_rejected(self):
        self._assert_rejected(self._token(secret="attacker-secret-attacker-secret-1234")[0])
        self._assert_rejected(self._token(exp=int(time.time()) - 10)[0])
        self._assert_rejected(self._token(aud="someone-else")[0])
        self._assert_rejected("not-a-jwt")
        b64 = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
        self._assert_rejected(f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': str(uuid.uuid4())})}.")

    def test_sec_002_users_cannot_read_each_others_progress(self):
        from backend.api import progress
        me, other = str(uuid.uuid4()), str(uuid.uuid4())
        with self.assertRaises(HTTPException) as ctx:
            progress._own(other, me)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(progress._own(me, me), me)

    def test_sec_002_every_non_public_route_requires_authentication(self):
        from fastapi.routing import APIRoute
        from backend.main import app
        from backend.security import get_current_user_id, validate_supabase_token
        public = ("/", "/health", "/api/v1/auth/", "/api/v1/content/", "/api/v1/packages/",
                  "/api/v1/leaderboard")

        def requires_auth(dep):
            return any(d.call in (get_current_user_id, validate_supabase_token) or requires_auth(d)
                       for d in dep.dependencies)

        unprotected = [f"{sorted(r.methods)} {r.path}" for r in app.routes
                       if isinstance(r, APIRoute) and not r.path.startswith(public)
                       and not requires_auth(r.dependant)]
        self.assertEqual(unprotected, [], "Routes exposing data without a valid token")


class SecretHandlingTests(unittest.TestCase):
    SKIP_DIRS = {"tests", ".venv", "venv", "__pycache__", "build", "dist"}

    def _py_files(self, *subdirs):
        roots = [APP_ROOT / d for d in subdirs] if subdirs else [APP_ROOT]
        for root in roots:
            for path in root.rglob("*.py"):
                if not self.SKIP_DIRS & set(path.relative_to(APP_ROOT).parts):
                    yield path

    def test_sec_006_no_hardcoded_credentials_in_source(self):
        patterns = {
            "JWT": re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\."),
            "AWS key": re.compile(r"AKIA[0-9A-Z]{16}"),
            "secret literal": re.compile(
                r"(?i)(service_role|secret|api_key|access_key)\w*\s*=\s*['\"][A-Za-z0-9/+_\-]{20,}['\"]"),
            "DB url with password": re.compile(r"postgres(?:ql)?(?:\+\w+)?://[^:\s/@'\"]+:[^@\s'\"{}$]+@"),
        }
        hits = [f"{p.relative_to(APP_ROOT)}:{i}: {label}"
                for p in self._py_files()
                for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1)
                for label, rx in patterns.items() if rx.search(line)]
        self.assertEqual(hits, [])

    def test_sec_006_desktop_client_never_touches_server_secrets(self):
        forbidden = ("SERVICE_ROLE", "S3_SECRET_KEY", "S3_ACCESS_KEY", "SUPABASE_JWT_SECRET")
        files = list(self._py_files("screens")) + [APP_ROOT / "backend" / n
                                                   for n in ("api_client.py", "auth_service.py", "sync_service.py")]
        hits = [f"{p.name}: {word}" for p in files
                for word in forbidden if word in p.read_text(encoding="utf-8", errors="ignore")]
        self.assertEqual(hits, [])

    def test_sec_006_env_file_is_git_ignored(self):
        gitignore = APP_ROOT.parent / ".gitignore"
        if not gitignore.is_file():
            self.skipTest("no .gitignore at repository root")
        self.assertRegex(gitignore.read_text(), r"(?m)^\s*\.env\s*$|^\s*\*\.env\s*$")

    def test_sec_006_api_errors_do_not_echo_raw_exceptions(self):
        rx = re.compile(r"detail\s*=\s*f[\"'][^\n]*\{\s*(?:str\(\s*)?(?:e|exc|error)\s*\)?\s*\}")
        files = list((APP_ROOT / "backend" / "api").glob("*.py")) + [APP_ROOT / "backend" / "main.py"]
        hits = [f"{p.name}:{i}" for p in files
                for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if rx.search(line)]
        self.assertEqual(hits, [], "Internal exception text (SQL, hosts) is returned to clients")

    def test_sec_008_https_enforced_in_production(self):
        from backend import api_client, auth_service
        with patch.object(api_client, "PRODUCTION", True):
            with self.assertRaises(RuntimeError):
                api_client.APIClient(api_client.APIConfig(base_url="http://insecure.example"))
            api_client.APIClient(api_client.APIConfig(base_url="https://secure.example"))
        with patch.object(auth_service, "PRODUCTION", True), \
                patch.object(auth_service, "SUPABASE_URL", "http://insecure.example"), \
                patch.object(auth_service, "SUPABASE_ANON_KEY", "anon"):
            with self.assertRaises(RuntimeError):
                auth_service.authenticate_with_supabase("a@example.com", "pw", establish_session=False)

    def test_sec_008_tls_verification_never_disabled(self):
        rx = re.compile(r"verify\s*=\s*False")
        hits = [p.name for p in self._py_files("backend", "screens")
                if rx.search(p.read_text(encoding="utf-8", errors="ignore"))]
        self.assertEqual(hits, [])


class RenderingSafetyTests(unittest.TestCase):
    def test_sec_005_user_text_is_rendered_as_plain_text(self):
        from PySide6.QtCore import Qt
        qt_app()
        from screens.dashboard.dashboard import DashboardWindow
        window = DashboardWindow()
        try:
            self.assertEqual(window.ui.welcomeLabel.textFormat(), Qt.TextFormat.PlainText)
        finally:
            window.close()
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()