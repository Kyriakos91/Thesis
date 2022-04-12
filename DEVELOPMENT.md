## Testing
The project comes with unit tests to make sure core logic is not affected. 
```bash
  pytest tests/
```

## Documentation
The project uses `pyreverse` in order to create the UML of classes and packages
```bash
  pyreverse *.py */*.py -o png
```

The project implements python documentation (__doc__) and uses pydoc to generate code documentation
```bash
  pydoc -w <package>
```

# Windows
- install Graphwiz (to output png when running pyreverse)

