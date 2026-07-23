"""Static content and business data for Barbearia BH, Porto.

TODO: confirm the business name with the client — the reviews and the only
logo asset supplied so far read "Donk / Donk — The Barbearshop", but the
client asked to keep "Barbearia BH" until they confirm tomorrow. Phone,
Instagram, and WhatsApp are still missing and marked TODO below. Service
descriptions and durations are placeholders: the service list itself
(names and prices) was confirmed by the client as "same as noble website
for now", but noble's site only ever had names and prices — no
descriptions or durations — so those two fields are estimates pending
real client input.
"""

SERVICES = [
    {"id": "classic-haircut", "name": "Corte clássico", "description": "", "price": 12, "duration_minutes": 30},
    {"id": "clipper-haircut", "name": "Corte máquina", "description": "", "price": 10, "duration_minutes": 20},
    {"id": "fade-haircut", "name": "Corte degradê", "description": "", "price": 14, "duration_minutes": 30},
    {"id": "haircut-beard", "name": "Corte e barba", "description": "", "price": 20, "duration_minutes": 45},
    {"id": "beard", "name": "Barba", "description": "", "price": 7, "duration_minutes": 15},
    {"id": "premium-beard", "name": "Barba premium", "description": "", "price": 10, "duration_minutes": 20},
]

# Confirmed by the client. Monday=0 ... Sunday=6.
BUSINESS_HOURS = {
    0: {"open": "10:00", "close": "20:00"},  # Monday
    1: {"open": "10:00", "close": "20:00"},  # Tuesday
    2: {"open": "10:00", "close": "20:00"},  # Wednesday
    3: {"open": "10:00", "close": "20:00"},  # Thursday
    4: {"open": "10:00", "close": "20:00"},  # Friday
    5: {"open": "09:00", "close": "20:00"},  # Saturday
    6: None,  # Sunday — closed
}

BUSINESS_INFO = {
    "name": "Barbearia BH",
    "address": "Rua de Costa Cabral 82, 4200-129 Porto, Portugal",
    # TODO: get phone, Instagram, and WhatsApp from the client.
    "phone": None,
    "instagram": None,
    "whatsapp": None,
}
