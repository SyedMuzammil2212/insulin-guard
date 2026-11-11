import os, subprocess, sys

def test_migration_up_and_down(tmp_path):
    env={**os.environ,'DATABASE_URL':f'sqlite:///{tmp_path}/migration.db','JWT_SECRET':'test-only-secret-with-at-least-32-characters'}
    root=os.path.dirname(os.path.dirname(__file__))
    for command in [('upgrade','head'),('downgrade','base'),('upgrade','head')]:
        subprocess.run([sys.executable,'-m','alembic',*command],cwd=root,env=env,check=True,capture_output=True)
