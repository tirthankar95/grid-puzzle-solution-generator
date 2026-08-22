import clingo


def solve(grid_puzzle: str):
    program = grid_puzzle
    ctl = clingo.Control()
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    solution = ""

    def show_model(model):
        nonlocal solution
        res = model.symbols(shown=True)
        solution = str(res)

    ctl.solve(on_model=show_model)
    return solution