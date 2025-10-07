from enum import Enum


class Step(Enum):
    CHALLENGE_DISCOVERY = "challenge_discovery"
    SEED_IMAGE_GENERATION = "seed_image_generation"
    COMPLETE = "complete"


class Gender(Enum):
    BOY = "boy"
    GIRL = "girl"
