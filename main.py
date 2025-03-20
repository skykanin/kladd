import polars as pl
import random
import string
from multiprocessing import Pool, cpu_count
from math import floor
from dapla_pseudo import Pseudonymize
import sys
from typing import Literal
from itertools import cycle

def random_string(length: int = 10) -> str:
    """Generate a single random alphanumeric string."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))

def gen_random_strings(n: int, length: int = 20) -> list[str]:
    """Generate a list of random alphanumeric strings using multiprocessing."""
    with Pool(cpu_count()) as pool:
        return pool.starmap(random_string, [(length,)] * n)

def gen_int() -> int:
    """Generate a single random integer between 0 and 100."""
    return floor(random.random() * 100)

def gen_random_ints(n: int) -> list[int]:
    with Pool(processes=cpu_count()) as pool:
        return pool.starmap(func=gen_int, iterable=[()] * n)

def generate_polars_dataframe(n: int, pseudo_type: Literal["sid", "default"]) -> pl.DataFrame:
    fnrs = cycle(["11854898347", "01839899544", "16910599481"])
    test_fnrs: list[str] | None = [next(fnrs) for _ in range(n)] if pseudo_type == "sid" else None 
    return pl.DataFrame({
        "fornavn": test_fnrs if pseudo_type == "sid" else gen_random_strings(n),
        "etternavn": test_fnrs if pseudo_type == "sid" else gen_random_strings(n),
        "alder": gen_random_ints(n)
    })

def gen_large_parquet(n: int, pseudo_type: Literal["sid", "default"]):
    path = f"/home/onyxia/work/kladd/input/{pseudo_type}_{n}_rows.parquet"
    print(f"Generating parquet file with {n} rows")
    df = generate_polars_dataframe(n, pseudo_type)
    print(df)
    df.write_parquet(path)
    print(f"File written to {path}")

def main(n: int, pseudo_type: Literal["sid", "default"]):
    path_read = f"/home/onyxia/work/kladd/input/{pseudo_type}_{n}_rows.parquet"
    path_write = f"/home/onyxia/work/kladd/output/{pseudo_type}_{n}_rows_pseudonymized.parquet"
    df = pl.read_parquet(path_read)
    print(f"Pseudonymizing DataFrame with shape f{df.shape}...")
    if pseudo_type == "sid":
        df = (
            Pseudonymize
            .from_polars(df)
            .on_fields("fornavn","etternavn")
            .with_stable_id()
            .run(timeout = 20 * 60)
            .to_polars()
        )
    else:
        df = (
            Pseudonymize
            .from_polars(df)
            .on_fields("fornavn","etternavn")
            .with_default_encryption()
            .run(timeout = 20 * 60)
            .to_polars()
        )

    print(df)
    df.write_parquet(path_write)
    print(f"File written to {path_write}")

if __name__ == "__main__":
    args = sys.argv[1:]
    match args:
        case ["gen", t, i]:
            n = floor(float(i) * 1_000_000)
            if t != "sid" and t != "default":
                print("Invalid pseudo_type argument")
                sys.exit(1)
            gen_large_parquet(n, t)
        case ["write", t, i]:
            n = floor(float(i) * 1_000_000)
            if t != "sid" and t != "default":
                print("Invalid pseudo_type argument")
                sys.exit(1)
            main(n, t)
        case _:
            print("Invalid argument passed")
            sys.exit(1)

