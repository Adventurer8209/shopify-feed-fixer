from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class GoogleShoppingProduct(BaseModel):
    # Жестко фиксируем SKU как строку
    sku: str = Field(..., min_length=1, description="Strict product SKU identifier")
    title: str = Field(..., max_length=150)
    
    # Цены всегда float
    price: float = Field(..., gt=0.0)
    currency: str = Field(default="USD", max_length=3)
    
    # Статусы наличия
    availability: str = Field(default="in_stock") 
    condition: str = Field(default="new")

    # 1. Защита ведущих нулей в SKU
    @field_validator("sku", mode="before")
    @classmethod
    def clean_sku(cls, value: any) -> str:
        if value is None:
            raise ValueError("SKU cannot be empty")
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError("SKU cannot be empty string")
        return cleaned

    # 2. Умная очистка американских и европейских цен
    @field_validator("price", mode="before")
    @classmethod
    def clean_and_parse_price(cls, value: any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Удаляем знаки валют и пробелы
            cleaned = re.sub(r"[^\d.,-]", "", value).strip()
            
            # Если есть и точка, и запятая
            if "," in cleaned and "." in cleaned:
                last_comma = cleaned.rfind(",")
                last_dot = cleaned.rfind(".")
                
                if last_comma > last_dot:
                    # Европейский формат: 1.250,00
                    cleaned = cleaned.replace(".", "")   
                    cleaned = cleaned.replace(",", ".")  
                else:
                    # Американский формат: 1,250.00
                    cleaned = cleaned.replace(",", "")   
            
            # Если есть только запятая (например, 12,50)
            elif "," in cleaned and "." not in cleaned:
                cleaned = cleaned.replace(",", ".")
                
            try:
                return float(cleaned)
            except ValueError:
                raise ValueError(f"Could not parse price from string: {value}")
                
        raise ValueError(f"Invalid price format: {value}")

    # 3. Приведение статуса наличия к стандарту Google Merchant
    @field_validator("availability")
    @classmethod
    def validate_google_availability(cls, value: str) -> str:
        allowed = {"in_stock", "out_of_stock", "preorder"}
        normalized = value.lower().strip().replace(" ", "_")
        
        mapping = {
            "available": "in_stock",
            "instock": "in_stock",
            "sold_out": "out_of_stock",
            "backorder": "preorder"
        }
        
        final_value = mapping.get(normalized, normalized)
        if final_value not in allowed:
            return "out_of_stock"
        return final_value