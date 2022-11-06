class SlashCommand:

    train = 1
    submit = 2
    time = 3
    claim = 4
    reject = 5
    approve = 6
    set_rank = 7
    wipe_state = 8

    all_values = [
        train,
        submit,
        time,
        claim,
        reject,
        approve,
        set_rank,
        wipe_state,
    ]

    names = {
        train: "train",
        submit: "submit",
        time: "time",
        claim: "claim",
        reject: "reject",
        approve: "approve",
        set_rank: "set-rank",
        wipe_state: "wipe-state",
    }

    descriptions = {
        train: "Begin a new training mission",
        submit: "Submit your most recent message for the current stage of a training mission",
        time: "Get the amount of time remaining for a training mission",
        claim: "Claim review of a mission",
        reject: "Reject a player's submission",
        approve: "Approve a player's submission",
        set_rank: "Set a uesr's rank",
        wipe_state: "Wipe the entire discord and db state",
    }

    def __init__(self, value: int):
        self.value = value

    @classmethod
    def all(cls):
        for value in cls.all_values:
            yield cls(value)

    def has_value(self, value: int):
        return self.value == value

    @classmethod
    def of_string(cls, s: str):
        for (value, name) in cls.names.items():
            if s == name:
                return cls(value)

    def name(self):
        return self.names[self.value]

    def description(self):
        return self.descriptions[self.value]

    def admin_only(self):
        return self.value in set([self.set_rank])
