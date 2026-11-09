"""Onde o tempo do fixture `seed` é gasto? (cProfile do comando de seed numa base de teste em memória)"""
import cProfile, io, os, pstats, sys, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
import django
django.setup()
from django.core.management import call_command
from django.test.utils import setup_databases, teardown_databases, setup_test_environment
setup_test_environment()
cfg = setup_databases(verbosity=0, interactive=False)
t = time.perf_counter(); pr = cProfile.Profile(); pr.enable(); call_command("seed"); pr.disable()
total = time.perf_counter() - t
print(f"seed completo: {total * 1000:.0f} ms")
s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(60)
lin = [l for l in s.getvalue().splitlines() if any(k in l for k in ("make_password", "argon2", "set_password", "get_or_create", "bulk_create", "hashers.py"))]
print("\n".join(l.strip()[:150] for l in lin[:8]))
teardown_databases(cfg, verbosity=0)
