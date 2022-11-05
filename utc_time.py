import datetime


class UtcTime:

    format = "%Y-%m-%d %H:%M:%S%z"

    def __init__(self, value):
        self.value = value.astimezone(datetime.timezone.utc)

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        return self.value.strftime(self.format)

    @classmethod
    def of_string(cls, s: str):
        return cls(value=datetime.datetime.strptime(s, cls.format))

    def diff_to_nearest_second(self, other):
        unrounded = self.value - other.value
        return datetime.timedelta(seconds=round(unrounded.total_seconds(), 0))

    @classmethod
    def now(cls):
        return cls(value=datetime.datetime.now())


class Test:
    @classmethod
    def arbitrary_date_in_timezone(cls, timezone: datetime.timezone):
        return UtcTime(datetime.datetime(year=2022, month=1, day=1, tzinfo=timezone))

    @classmethod
    def run_of_string(cls, s: str, expected: UtcTime):
        assert UtcTime.of_string(s) == expected

    @classmethod
    def of_string_utc(cls):
        cls.run_of_string(
            "2022-01-01 00:00:00+0000",
            expected=cls.arbitrary_date_in_timezone(timezone=datetime.timezone.utc),
        )

    @classmethod
    def of_string_minus_offset(cls):
        cls.run_of_string(
            "2022-01-01 00:00:00-0100",
            expected=cls.arbitrary_date_in_timezone(
                timezone=datetime.timezone(offset=datetime.timedelta(hours=-1)),
            ),
        )

    @classmethod
    def of_string_plus_offset(cls):
        cls.run_of_string(
            "2022-01-01 00:00:00+0100",
            expected=cls.arbitrary_date_in_timezone(
                timezone=datetime.timezone(offset=datetime.timedelta(hours=1)),
            ),
        )

    @classmethod
    def run_all_of_string(cls):
        cls.of_string_utc()
        cls.of_string_minus_offset()
        cls.of_string_plus_offset()

    @classmethod
    def run_roundtrip(cls, timezone: datetime.timezone):
        utc_time = cls.arbitrary_date_in_timezone(timezone)
        parsed = UtcTime.of_string(str(utc_time))
        assert parsed == utc_time

    @classmethod
    def roundtrip_utc(cls):
        cls.run_roundtrip(timezone=datetime.timezone.utc)

    @classmethod
    def roundtrip_minus_offset(cls):
        cls.run_roundtrip(
            timezone=datetime.timezone(offset=datetime.timedelta(hours=-1))
        )

    @classmethod
    def roundtrip_plus_offset(cls):
        cls.run_roundtrip(
            timezone=datetime.timezone(offset=datetime.timedelta(hours=1))
        )

    @classmethod
    def run_all_roundtrip(cls):
        cls.roundtrip_utc()
        cls.roundtrip_minus_offset()
        cls.roundtrip_plus_offset()

    @classmethod
    def run_diff_to_nearest_second(
        cls, *, earlier: UtcTime, later: UtcTime, expected: datetime.timedelta
    ):
        assert later.diff_to_nearest_second(earlier) == expected

    @classmethod
    def diff_to_nearest_second_same_time(cls):
        utc_time = cls.arbitrary_date_in_timezone(timezone=datetime.timezone.utc)

        cls.run_diff_to_nearest_second(
            earlier=utc_time, later=utc_time, expected=datetime.timedelta(seconds=0)
        )

    @classmethod
    def diff_to_nearest_second_rounds(cls):
        earlier = cls.arbitrary_date_in_timezone(timezone=datetime.timezone.utc)
        later = UtcTime(
            earlier.value + datetime.timedelta(seconds=35, milliseconds=700)
        )

        cls.run_diff_to_nearest_second(
            earlier=earlier,
            later=later,
            expected=datetime.timedelta(seconds=36),
        )

    @classmethod
    def run_all_diff_to_nearest_second(cls):
        cls.diff_to_nearest_second_same_time()
        cls.diff_to_nearest_second_rounds()

    @classmethod
    def run_all(cls):
        cls.run_all_of_string()
        cls.run_all_roundtrip()
        cls.run_all_diff_to_nearest_second()


Test.run_all()
