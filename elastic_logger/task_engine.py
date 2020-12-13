import asyncio


class TaskEngine:

    # The constructor initialize the TaskEngine and
    # sets up various counters to track started, pending
    # and completed tasks
    # self.stopped indicates if the engine has been stopped
    def __init__(self, max_tasks=10, monitor=False, logger=None):
        self.loop = asyncio.get_event_loop()
        self.started = 0
        self.pending = 0
        self.completed = 0
        self.stopped = False
        self.max_tasks = max_tasks
        self.logger = logger
        # Create a task instance of the __monitor task
        # if the self.monitor == True
        self.monitor = monitor
        if self.monitor:
            self.loop.create_task(self.__monitor())

    # Run the task engine until all tasks have completed
    def run(self, driver, *args, **kwargs):
        self.loop.run_until_complete(self.__run(driver, *args, **kwargs))

    # Initiate shutdown of the task engine. This does not
    # stop any tasks - it just sets stopped to True
    async def stop(self):
        print("\033[1K\rStopping...")
        self.stopped = True
        # Wait for the monitor task to shut down
        while self.monitor:
            await asyncio.sleep(0.01)

    # returns True if running (not stopped)
    def running(self):
        return not self.stopped

    # Starts a new task. This function ensures
    # that the maximum number of concurrent tasks
    # is not exceeded
    async def start_task(self, task, *args, **kwargs):
        # if max_tasks are already running, then sleep
        # briefly and wait for the number to drop
        while self.running() and self.pending >= self.max_tasks:
            await asyncio.sleep(0.005)
        # Don't start the task if the engine is set to stop
        if self.running():
            # Increment the counters
            self.__begin_task()
            # and start the task on the async event loop
            self.loop.create_task(self.__start_task(task, *args, **kwargs))
        else:
            print("\033[1K\rNot starting task: engine stopped")

    # Sleep until there no pending tasks
    async def run_until_complete(self):
        while self.pending > 0:
            await asyncio.sleep(0.01)

    # Internal method to run the TaskEngine
    async def __run(self, driver, *args, **kwargs):
        try:
            # Run the user's async engine task
            await driver(self, *args, **kwargs)
            # wait for all tasks to finish - the engine
            # task will often just create tasks then finish
            await self.run_until_complete()
        finally:
            await self.stop()
            # Close the logger
            if self.logger:
                await self.logger.close()

    # Internal method to launch a task
    async def __start_task(self, task, *args, **kwargs):
        try:
            # Launch the async task and wait for it to finish
            await task(*args, **kwargs)
        finally:
            # Update the task counters
            self.__end_task()

    # update task counters at start of task
    def __begin_task(self):
        self.pending += 1
        self.started += 1

    # update task counters at end of task
    def __end_task(self):
        self.pending -= 1
        self.completed += 1

    # The __monitor function updates task stats
    # every 0.5 seconds
    # the "\033[1K\r" escape sequence clears the console line
    # up to the cursor, then sets the cursor at the beginning of the line
    # (without a line feed). This allows for the dynamic status
    # updates on one console line
    async def __monitor(self):
        # Run until stopped
        while self.running():
            print("\033[1K\rTask Monitor: Started: {} : Pending: {} : Completed: {}".format(
                self.started, self.pending, self.completed), end="")
            await asyncio.sleep(0.5)
        # display final counts
        print("\033[1K\rTask Monitor: Started: {} : Pending: {} : Completed: {}".format(
            self.started, self.pending, self.completed))
        print("TaskEngine stopped.")
        # allow shutdown to finalize
        self.monitor = False
