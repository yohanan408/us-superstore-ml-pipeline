from pydantic import BaseModel, Field

class CheckoutCartRequest(BaseModel):
    # Enforce strict float data type at ingestion to prevent truncations
    Discount: float = Field(..., description="Float markdown percentage (0.00 to 0.80)", example=0.20)
    
    # Missing continuous and categorical features required for model matrix matching
    Sales: float = Field(..., description="Raw transaction revenue value in dollars", example=1250.00)
    Quantity: float = Field(..., description="Total product item volume in cart", example=5.0)
    Processing_Time_Days: float = Field(..., description="Estimated warehouse handling duration", example=4.0)
    Category_Furniture: int = Field(0, description="One-hot encoded flag for Furniture tier", example=0)
    Category_Office_Supplies: int = Field(0, description="One-hot encoded flag for Office Supplies tier", example=1)

