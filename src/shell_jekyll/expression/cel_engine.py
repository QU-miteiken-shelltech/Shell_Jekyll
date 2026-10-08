class CELEngine:
    def __init__(self,
                 cel_expression: str
                 ):
        """Compile a CEL expression.

        [Changed] ``cel_expr_python`` is imported here instead of at module
        top, so the application starts even when that package is missing
        (only running a CEL expression then fails).
        """
        from cel_expr_python import cel
        cel_env = cel.NewEnv(
            variables={
                "frame": cel.Type.INT,
                "seq_count": cel.Type.INT,
                "loop_count": cel.Type.INT,
                "cframe": cel.Type.INT
                }
            )
        self.expr = cel_env.compile(cel_expression)

    def run_cel(self,
                data: dict
                ) -> str:
        rtn = self.expr.eval(data=data).value()
        return rtn
