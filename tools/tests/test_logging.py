#!/home/slate/SLATE/venv/bin/python3

from faker import Faker
import random

from core.logging import log_event

# Test logging:

fake = Faker()
for n in range(100):
    summary = fake.sentence()
    details = fake.sentence()
    category = random.choice([
                                "access",
                                "activity",
                                "auth",
                                "debug",
                                "entity_history",
                                "error",
                                "tests"
                            ])
    log_event(category, summary, details)
