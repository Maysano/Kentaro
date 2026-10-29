"""Compatibility imports for the course's former LearningPortfolio API."""
from kentaro.design.portfolio import content_hash, load_portfolio, make_claim as claim, save_portfolio, validate_portfolio
from kentaro.scenarios.udemy_masterclass import starting_portfolio as create_case_portfolio

__all__ = ["claim", "content_hash", "create_case_portfolio", "load_portfolio", "save_portfolio", "validate_portfolio"]
