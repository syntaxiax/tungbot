# Shared state between giveaway.py and giveaway_cancel.py
# message_id (int) -> {"task": asyncio.Task, "view": GiveawayView}
active_giveaways: dict = {}
