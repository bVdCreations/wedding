from fastapi import APIRouter

from .features.get_guest_info.router import router as get_guest_info_router
from .features.update_rsvp.router import router as update_rsvp_router

router = APIRouter()

router.include_router(get_guest_info_router)
router.include_router(update_rsvp_router)
