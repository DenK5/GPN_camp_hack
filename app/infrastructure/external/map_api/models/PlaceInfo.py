from pydantic import BaseModel, Field, AliasPath, BeforeValidator
import re
import typing as t
from app.infrastructure.external.map_api.models.Point import Point


def collect_rubrics(rubrics: dict[str, t.Any]) -> list[str]:
    return [rubric['name'] for rubric in rubrics]


def get_avg_lunch_cost(stop_factors: list[dict[str, str]]) -> int:
    for stop_factor in stop_factors:
        if stop_factor.get('tag') == 'food_service_avg_price':
            return int(re.search('\d+', stop_factor.get('name')).group(0))
    return -1


def get_avg_business_lunch_cost(stop_factors: list[dict[str, str]]) -> int:
    for stop_factor in stop_factors:
        if stop_factor.get('tag') == 'food_service_lunch_cost':
            return int(re.search('\d+', stop_factor.get('name')).group(0))
    return -1


def get_cuisines(stop_factors: list[dict[str, str]]) -> list[str]:
    cuisines = []
    for stop_factor in stop_factors:
        if 'food_service_food_' in stop_factor.get('tag', ''):
            cuisines.append(stop_factor.get('name'))
    return cuisines


class PlaceInfo(BaseModel):
    place_id: str = Field(validation_alias='id')
    address_name: str
    place_name: str = Field(validation_alias='name')
    point: Point
    general_rating: float = Field(validation_alias=AliasPath('reviews', 'general_rating'))
    rubrics: t.Annotated[list[str], BeforeValidator(collect_rubrics)]
    avg_lunch_cost: t.Annotated[int, BeforeValidator(get_avg_lunch_cost)] = Field(-1, validation_alias=AliasPath('context', 'stop_factors'))
    avg_business_lunch_cost: t.Annotated[int, BeforeValidator(get_avg_business_lunch_cost)] = Field(-1, validation_alias=AliasPath('context', 'stop_factors'))
    cuisines: t.Annotated[list[str], BeforeValidator(get_cuisines)] = Field(-1, validation_alias=AliasPath('context', 'stop_factors'))
