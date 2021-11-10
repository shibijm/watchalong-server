from typing import Callable, Any, Coroutine
import asyncio

class AsyncTimer:

	def __init__(self, delay: int, callback: Callable[..., Coroutine[None, None, Any]], *args: Any, **kwargs: Any) -> None:
		"""
		Schedules coroutine function `callback` to be called after `delay` seconds.

		Parameters
		----------
		delay: int
			The delay in seconds before calling the callback.
		callback: Callable
			The coroutine function to be called after the delay.
		*args
			Arguments to be passed to the callback.
		**kwargs
			Keyword arguments to be passed to the callback.
		"""
		self.task = asyncio.create_task(self.delayedCallback(delay, callback, *args, **kwargs))

	def cancel(self) -> None:
		"""
		Cancels the scheduled callback.
		"""
		self.task.cancel()

	async def delayedCallback(self, delay: int, callback: Callable[..., Coroutine[None, None, Any]], *args: Any, **kwargs: Any) -> None:
		await asyncio.sleep(delay)
		await callback(*args, **kwargs)
