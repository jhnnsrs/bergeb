from contextvars import ContextVar
from rich.console import ConsoleRenderable
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from bergen.console import console

current_monitor: ContextVar["Monitor"] = ContextVar('current_monitor', default=None)


class Monitor:

    def __init__(self, title="Monitor", progress=False) -> None:
        """Monitor allows you to monitor the progress of what is happenening inside your application


        Args:
            title (str, optional): The Title of this Monitor (Is the Panels Title). Defaults to "Monitor".
            progress (bool, optional): Do you want to monitor the progress of assignments and reservations? Defaults to False.
        """
        self.columns = Table.grid(expand=True)
        self.columns.add_column()
        self.progress = progress
        self.panel = Panel(self.columns, title=title)
        self.live = Live(self.panel, refresh_per_second=4, console=console)


    def addRow(self, renderable: ConsoleRenderable):
        self.columns.add_row(renderable)

    def __aenter__(self):
        '''Convenience Method'''
        return self.__aenter__()

    def __aexit__(self,*args,**kwargs):
        self.__exit__(*args,**kwargs)

    def __enter__(self):
        current_monitor.set(self)
        self.live.__enter__()
        return self


    def __exit__(self, *args, **kwargs):
        self.live.__exit__(*args, **kwargs)
        current_monitor.set(None)
