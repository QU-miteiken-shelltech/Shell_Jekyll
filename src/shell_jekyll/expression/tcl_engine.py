from shell_jekyll.io.io_sjproj import IO_sjproj
from shell_jekyll import gb_var as gb_var_script

gb_var = gb_var_script.get_gbvar_ctx()
gb_var_full = gb_var_script.get_gbvar_full()

class TCLEngine:
    def __init__(self, expression: str | None = None):
        """Create a TCL interpreter bound to a script.

        [Changed]
        * ``tkinter`` is imported here instead of at module top, so a Python
          without Tk no longer breaks the import of the whole application
          (``main_win_io`` imports this module at start-up).
        * ``self.expression`` is always defined.  It used to be missing when no
          project was saved yet (early ``return``), so ``get_procs`` /
          ``run_tcl`` raised ``AttributeError``.
        * ``expression`` may be passed directly (for scripting / tests); when
          omitted the script is read from the saved project, as before.
        """
        import tkinter
        self.tcl_intepreter = tkinter.Tcl()
        self.expression = expression
        if expression is not None:
            return
        reading_path = gb_var.saving_path if gb_var_script.is_configured() else None
        if reading_path is None:
            print("TCL Engine used when reading_path is None")
            return
        self.expression = IO_sjproj.read_sjproj(
            reading_path=str(reading_path),
            reading_attr="expression"
        )

    def get_procs(self) -> list[str]:
        if self.expression is None:
            return []
        self.tcl_intepreter.eval(self.expression)
        all_procs = self.tcl_intepreter.eval("info procs").split()
        system_procs = {
            'unknown', 'auto_load', 'auto_load_index', 'auto_import',
            'auto_execok', 'auto_qualify', 'tclLog'
            }
        function_procs = [p for p in all_procs if p not in system_procs]
        return function_procs

    def run_tcl(self,
                func_name: str,
                **arguments
                ) -> str:
        """Evaluate the script, then call ``func_name`` with the key/value list ``arguments``.

        Unchanged behaviour (the script is re-evaluated on every call, the
        arguments are passed as ONE flattened ``key value key value ...`` list).
        Only added: a clear error when there is no script.
        """
        if self.expression is None:
            raise RuntimeError("No TCL expression is stored in the project")
        self.tcl_intepreter.eval(self.expression)
        tcl_rtn = self.tcl_intepreter.call(
            func_name,
            [item for pair in arguments.items() for item in pair]
        )
        return str(tcl_rtn)
