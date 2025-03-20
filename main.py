import polars as pl
import random
import string
from multiprocessing import Pool, cpu_count
from math import floor
from dapla_pseudo import Pseudonymize
import sys
import os

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

def generate_polars_dataframe(n: int) -> pl.DataFrame:
    return pl.DataFrame({
        "fornavn": gen_random_strings(n),
        "etternavn": gen_random_strings(n),
        "alder": gen_random_ints(n)
    })

def gen_large_parquet(n: int):
    path = f"/home/onyxia/work/kladd/output/{n}_rows.parquet"
    print(f"Generating parquet file with {n} rows")
    df = generate_polars_dataframe(n)
    df.write_parquet(path)
    print(f"File written to {path}")

def main(n: int):
    path_read = f"/home/onyxia/work/kladd/output/{n}_rows.parquet"
    path_write = f"/home/onyxia/work/kladd/output/{n}_rows_pseudonymized.parquet"
    df = pl.read_parquet(path_read)
    print(f"Pseudonymizing DataFrame with shape f{df.shape}...")
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
        case ["gen", i]:
            n = floor(float(i) * 1_000_000)
            gen_large_parquet(n)
        case ["write", i]:
            n = floor(float(i) * 1_000_000)
            main(n)
        case _:
            print("Invalid argument passed")
            sys.exit(1)

