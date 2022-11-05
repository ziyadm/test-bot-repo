import copy
import json
from typing import Dict, List, Set, Tuple


class Fields:
    pass


class Record:
    def __init__(self, **provided_fields):
        for field in self.__annotations__.keys():
            if field not in provided_fields:
                raise AttributeError(f"""missing field {field}""")

            setattr(self, field, provided_fields[field])

    def __eq__(self, other):
        for field in self.__annotations__.keys():
            if getattr(self, field) != getattr(other, field):
                return False

        return True

    def to_dict(self):
        data = {}

        def maybe_nested_value(value):
            if hasattr(value, "to_string"):
                return value.to_string()

            if not hasattr(value, "to_dict"):
                return value

            return value.to_dict()

        for (field, field_cls) in self.__annotations__.items():
            field_data = getattr(self, field)

            if not hasattr(field_cls, "_name"):
                data[field] = maybe_nested_value(field_data)
            elif field_cls._name in (List._name, Set._name, Tuple._name):
                data[field] = [maybe_nested_value(value) for value in field_data]
            elif field_cls._name == Dict._name:
                data[field] = {
                    key: maybe_nested_value(value)
                    for (key, value) in field_data.items()
                }

        return data

    def to_json_serialized_dict(self):
        return {key: json.dumps(value) for (key, value) in self.to_dict().items()}

    @classmethod
    def of_dict(cls, fields):
        data = {}

        def parse_maybe_nested_value(value, expected_type):
            if hasattr(expected_type, "of_string"):
                return expected_type.of_string(value)

            if not hasattr(expected_type, "of_dict"):
                return expected_type(value)

            return expected_type.of_dict(value)

        for (field, field_data) in fields.items():
            field_cls = cls.__annotations__[field]

            if not hasattr(field_cls, "_name"):
                data[field] = parse_maybe_nested_value(field_data, field_cls)
            elif field_cls._name == Tuple._name:
                data[field] = tuple(
                    [
                        parse_maybe_nested_value(value, expected_value_type)
                        for (value, expected_value_type) in zip(
                            field_data, field_cls.__args__
                        )
                    ]
                )
            elif field_cls._name in (List._name, Set._name):
                (expected_value_type,) = field_cls.__args__
                parsed_data = [
                    parse_maybe_nested_value(value, expected_value_type)
                    for value in field_data
                ]
                if field_cls._name == Set._name:
                    data[field] = set(parsed_data)
                else:
                    data[field] = parsed_data
            elif field_cls._name == Dict._name:
                (expected_key_type, expected_value_type) = field_cls.__args__
                data[field] = {
                    expected_key_type(key): parse_maybe_nested_value(
                        value, expected_value_type
                    )
                    for (key, value) in field_data.items()
                }

        return cls(**data)

    @classmethod
    def of_json_serialized_dict(cls, json_serialized_dict: Dict[str, str]):
        return cls.of_dict(
            {key: json.loads(value) for (key, value) in json_serialized_dict.items()}
        )

    def update(self, updates):
        updated = copy.deepcopy(self)

        for field, value in updates.items():
            setattr(updated, field, value)

        return updated

    # TODO: i think we need to use a metaclass to avoid having to do this, but this seems fine for now
    @classmethod
    def field(cls):
        fields = Fields()
        for field in cls.__annotations__.keys():
            setattr(fields, field, field)
        return fields


class Test_str_record(Record):
    str_field: str


class Test_int_record(Record):
    int_field: int


class Test_float_record(Record):
    float_field: float


class Test_bool_record(Record):
    bool_field: bool


class Test_list_record(Record):
    list_field: List[int]


class Test_nested_list_record(Record):
    nested_list_field: List[Test_int_record]


class Test_tuple_record(Record):
    tuple_field: Tuple[int, str]


class Test_nested_tuple_record(Record):
    nested_tuple_field: Tuple[int, Test_int_record]


class Test_set_record(Record):
    set_field: Set[int]


class Test_dict_record(Record):
    dict_field: Dict[int, str]


class Test_nested_dict_record(Record):
    nested_dict_field: Dict[int, Test_int_record]


class Test_nested_record(Record):
    nested_record: Test_int_record


class Test_record_with_multiple_fields(Record):
    str_field: str
    int_field: int


class Test_variant:
    variant_a = 1
    variant_b = 2

    all_values = [
        variant_a,
        variant_b,
    ]
    name = {variant_a: "variant_a", variant_b: "variant_b"}

    def __init__(self, value: int):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def to_string(self):
        return self.name[self.value]

    @classmethod
    def of_string(cls, s: str):
        for (value, name) in cls.name.items():
            if s == name:
                return cls(value)


class Test_record_with_custom_serialization(Record):
    variant_field: Test_variant


class Test:
    test_int_record = Test_int_record(
        int_field=1,
    )

    @classmethod
    def run_roundtrip(cls, test_record_cls, test_record):
        assert (
            test_record_cls.of_json_serialized_dict(
                test_record.to_json_serialized_dict()
            )
            == test_record
        )

    @classmethod
    def roundtrip_str(cls):
        cls.run_roundtrip(
            Test_str_record,
            Test_str_record(
                str_field="test-str-field",
            ),
        )

    @classmethod
    def roundtrip_int(cls):
        cls.run_roundtrip(
            Test_int_record,
            Test_int_record.of_json_serialized_dict(
                cls.test_int_record.to_json_serialized_dict()
            ),
        )

    @classmethod
    def roundtrip_float(cls):
        cls.run_roundtrip(
            Test_float_record,
            Test_float_record(
                float_field=10.0,
            ),
        )

    @classmethod
    def roundtrip_bool(cls):
        cls.run_roundtrip(
            Test_bool_record,
            Test_bool_record(
                bool_field=False,
            ),
        )

    @classmethod
    def roundtrip_list(cls):
        cls.run_roundtrip(
            Test_list_record,
            Test_list_record(
                list_field=[1, 2, 3],
            ),
        )

    @classmethod
    def roundtrip_nested_list(cls):
        cls.run_roundtrip(
            Test_nested_list_record,
            Test_nested_list_record(
                nested_list_field=[
                    cls.test_int_record,
                    cls.test_int_record,
                ],
            ),
        )

    @classmethod
    def roundtrip_tuple(cls):
        cls.run_roundtrip(
            Test_tuple_record,
            Test_tuple_record(
                tuple_field=(1, "test-tuple"),
            ),
        )

    @classmethod
    def roundtrip_nested_tuple(cls):
        cls.run_roundtrip(
            Test_nested_tuple_record,
            Test_nested_tuple_record(
                nested_tuple_field=(1, cls.test_int_record),
            ),
        )

    @classmethod
    def roundtrip_set(cls):
        cls.run_roundtrip(
            Test_set_record,
            Test_set_record(
                set_field=set([1, 2, 3]),
            ),
        )

    @classmethod
    def roundtrip_dict(cls):
        cls.run_roundtrip(
            Test_dict_record,
            Test_dict_record(
                dict_field={1: "1", 2: "2"},
            ),
        )

    @classmethod
    def roundtrip_nested_dict(cls):
        cls.run_roundtrip(
            Test_nested_dict_record,
            Test_nested_dict_record(
                nested_dict_field={1: cls.test_int_record, 2: cls.test_int_record},
            ),
        )

    @classmethod
    def roundtrip_nested(cls):
        cls.run_roundtrip(
            Test_nested_record,
            Test_nested_record(
                nested_record=cls.test_int_record,
            ),
        )

    @classmethod
    def roundtrip_record_with_custom_serialization(cls):
        cls.run_roundtrip(
            Test_record_with_custom_serialization,
            Test_record_with_custom_serialization(
                variant_field=Test_variant(Test_variant.variant_a),
            ),
        )

    @classmethod
    def run_all_roundtrip(cls):
        cls.roundtrip_str()
        cls.roundtrip_int()
        cls.roundtrip_float()
        cls.roundtrip_bool()
        cls.roundtrip_list()
        cls.roundtrip_nested_list()
        cls.roundtrip_tuple()
        cls.roundtrip_nested_tuple()
        cls.roundtrip_set()
        cls.roundtrip_dict()
        cls.roundtrip_nested_dict()
        cls.roundtrip_nested()
        cls.roundtrip_record_with_custom_serialization()

    @classmethod
    def run_update(cls, *, original, updates, expected):
        assert original.update(updates) == expected

    @classmethod
    def update_no_fields(cls):
        original = Test_int_record(int_field=0)
        cls.run_update(original=original, updates={}, expected=original)

    @classmethod
    def update_one_field(cls):
        cls.run_update(
            original=Test_int_record(int_field=0),
            updates={Test_int_record.field().int_field: 5},
            expected=Test_int_record(int_field=5),
        )

    @classmethod
    def update_many_fields(cls):
        cls.run_update(
            original=Test_record_with_multiple_fields(
                str_field="str-field", int_field=0
            ),
            updates={
                Test_record_with_multiple_fields.field().str_field: "new-str-field",
                Test_record_with_multiple_fields.field().int_field: 5,
            },
            expected=Test_record_with_multiple_fields(
                str_field="new-str-field", int_field=5
            ),
        )

    @classmethod
    def run_all_update(cls):
        cls.update_no_fields()
        cls.update_one_field()
        cls.update_many_fields()

    @classmethod
    def run_all(cls):
        cls.run_all_roundtrip()
        cls.run_all_update()


Test.run_all()
