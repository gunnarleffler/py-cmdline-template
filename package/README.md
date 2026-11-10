# Example package

Optional packaging starter, separate from the root script project.
Rename the project in `pyproject.toml` and the `example_pkg` directory before use.
Update the wheel package path to match.

Build from the repository root:

```sh
uv build ./package
```

For an installable CLI, add a `main()` function to your package and declare it:

```toml
[project.scripts]
my-command = "example_pkg:main"
```

See the [Python packaging guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
