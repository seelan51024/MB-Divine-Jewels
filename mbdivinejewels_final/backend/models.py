from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    token: str
    email: str

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int = 0
    cat: str = "Other"
    mat: str = "Gold plate"
    size: Optional[str] = ""
    description: Optional[str] = ""
    photo: Optional[str] = None
    photos: Optional[str] = None  # JSON array of base64 images

class ProductUpdate(BaseModel):
    name: str
    price: float
    stock: int
    cat: str
    mat: str
    size: Optional[str] = ""
    description: Optional[str] = ""
    photo: Optional[str] = None
    photos: Optional[str] = None

class PaymentSettings(BaseModel):
    upi: Optional[str] = ""
    upiName: Optional[str] = ""
    bankName: Optional[str] = ""
    bankAcc: Optional[str] = ""
    bankIFSC: Optional[str] = ""
    bankBank: Optional[str] = ""
    qr: Optional[str] = None
    note: Optional[str] = ""
    cod: Optional[bool] = False
    shippingFee: Optional[float] = 0
    freeShippingAbove: Optional[float] = 0

class OrderCreate(BaseModel):
    id: str
    items: list
    total: float
    pay: str
    time: str
    cart: Optional[Dict[str, Any]] = None

class CustomerOrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    customer_note: Optional[str] = ""
    items: List[Dict[str, Any]]
    total: float
    shipping_fee: Optional[float] = 0
    payment_method: Optional[str] = "upi"
    payment_proof: Optional[str] = None   # base64 screenshot
    payment_txn_id: Optional[str] = ""
    time: str

class UpdateStatusRequest(BaseModel):
    new_status: str

class StoreSettings(BaseModel):
    storeName: Optional[str] = "MB Divine Jewels"
    tagline: Optional[str] = "Style, Starts Here"
    announcement: Optional[str] = "✦ Free Shipping on All Orders Across India ✦"
    heroEyebrow: Optional[str] = ""
    heroTitle: Optional[str] = ""
    heroBtn: Optional[str] = "Shop Collection →"
    heroImages: Optional[list] = []      # list of base64 image strings (up to 5)
    heroImage: Optional[str] = None      # legacy single image (kept for backward compat)
    feat1Title: Optional[str] = "Free Delivery"
    feat1Sub: Optional[str] = "Pan India"
    feat2Title: Optional[str] = "Secure Payment"
    feat2Sub: Optional[str] = "UPI / Bank"
    feat3Title: Optional[str] = "Quality Assured"
    feat3Sub: Optional[str] = "Premium Gold Plate"
    feat4Title: Optional[str] = "Easy Returns"
    feat4Sub: Optional[str] = "7-Day Policy"
    footerTagline: Optional[str] = "Style, Starts Here"
    footerAddress: Optional[str] = "Tamil Nadu, India"
    whatsapp: Optional[str] = ""
    instagram: Optional[str] = ""
    shippingPolicy: Optional[str] = ""
    refundPolicy: Optional[str] = ""
    privacyPolicy: Optional[str] = ""

class StorySection(BaseModel):
    image: Optional[str] = None          # base64
    title: Optional[str] = ""
    body: Optional[str] = ""
    btnText: Optional[str] = "Our Story ✦"

class Testimonial(BaseModel):
    name: Optional[str] = ""
    location: Optional[str] = ""
    text: Optional[str] = ""
    stars: Optional[int] = 5

class TestimonialsSection(BaseModel):
    items: Optional[List[Any]] = []

class GallerySection(BaseModel):
    images: Optional[List[str]] = []    # list of base64 strings (up to 8)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
