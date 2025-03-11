"""
External data integration module.

This module provides integration with external data sources.
"""
from .investpy import InvestpyClient
from .forex_factory import ForexFactoryClient
from .social_media import SocialMediaClient

__all__ = ['InvestpyClient', 'ForexFactoryClient', 'SocialMediaClient']
