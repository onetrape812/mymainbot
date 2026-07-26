import math
from datetime import datetime, timezone

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, Review, Portfolio, Order
from bot.config import PAGE_SIZE, REVIEWS_PER_PAGE


async def get_or_create_user(session: AsyncSession, user_id: int, username: str | None, full_name: str) -> User:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(user_id=user_id, username=username, full_name=full_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        user.username = username
        user.full_name = full_name
        await session.commit()
    return user


async def add_review(session: AsyncSession, user_id: int, rating: int, text: str) -> Review:
    review = Review(user_id=user_id, rating=rating, text=text, status="pending")
    session.add(review)
    await session.commit()
    await session.refresh(review)
    return review


async def get_pending_reviews(session: AsyncSession) -> list[Review]:
    result = await session.execute(
        select(Review).where(Review.status == "pending").order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())


async def approve_review(session: AsyncSession, review_id: int) -> Review | None:
    result = await session.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if review:
        review.status = "approved"
        await session.commit()
    return review


async def reject_review(session: AsyncSession, review_id: int) -> Review | None:
    result = await session.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if review:
        review.status = "rejected"
        await session.commit()
    return review


async def delete_review(session: AsyncSession, review_id: int) -> bool:
    result = await session.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if review:
        await session.delete(review)
        await session.commit()
        return True
    return False


async def get_all_reviews(session: AsyncSession) -> list[Review]:
    result = await session.execute(
        select(Review).order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())


async def get_approved_reviews(session: AsyncSession, page: int = 0) -> tuple[list[Review], int]:
    count_q = select(func.count()).select_from(Review).where(Review.status == "approved")
    total = (await session.execute(count_q)).scalar() or 0
    result = await session.execute(
        select(Review)
        .where(Review.status == "approved")
        .order_by(Review.created_at.desc())
        .offset(page * REVIEWS_PER_PAGE)
        .limit(REVIEWS_PER_PAGE)
    )
    return list(result.scalars().all()), total


async def get_review_stats(session: AsyncSession) -> tuple[float, int]:
    result = await session.execute(
        select(func.avg(Review.rating), func.count()).where(Review.status == "approved")
    )
    row = result.one()
    avg = float(row[0]) if row[0] else 0.0
    count = row[1] or 0
    return avg, count


async def get_portfolio_page(session: AsyncSession, page: int = 0) -> tuple[list[Portfolio], int]:
    count_q = select(func.count()).select_from(Portfolio)
    total = (await session.execute(count_q)).scalar() or 0
    result = await session.execute(
        select(Portfolio).order_by(Portfolio.created_at.desc()).offset(page * PAGE_SIZE).limit(PAGE_SIZE)
    )
    return list(result.scalars().all()), total


async def get_all_portfolio(session: AsyncSession) -> list[Portfolio]:
    result = await session.execute(select(Portfolio).order_by(Portfolio.created_at.desc()))
    return list(result.scalars().all())


async def get_portfolio_categories(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(Portfolio.category).where(Portfolio.category.isnot(None)).group_by(Portfolio.category)
    )
    return [row[0] for row in result.all()]


async def get_portfolio_by_category(session: AsyncSession, category: str) -> list[Portfolio]:
    result = await session.execute(
        select(Portfolio).where(Portfolio.category == category).order_by(Portfolio.created_at.desc())
    )
    return list(result.scalars().all())


async def get_portfolio_item(session: AsyncSession, item_id: int) -> Portfolio | None:
    result = await session.execute(select(Portfolio).where(Portfolio.id == item_id))
    return result.scalar_one_or_none()


async def add_portfolio_item(session: AsyncSession, title: str, description: str, link: str | None, category: str | None) -> Portfolio:
    item = Portfolio(title=title, description=description, link=link, category=category)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def delete_portfolio_item(session: AsyncSession, item_id: int) -> bool:
    result = await session.execute(select(Portfolio).where(Portfolio.id == item_id))
    item = result.scalar_one_or_none()
    if item:
        await session.delete(item)
        await session.commit()
        return True
    return False


async def create_order(session: AsyncSession, user_id: int, description: str, budget: str | None, contact: str) -> Order:
    order = Order(user_id=user_id, description=description, budget=budget, contact=contact)
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_user_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar() or 0


async def get_review_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Review))
    return result.scalar() or 0


async def get_order_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Order))
    return result.scalar() or 0
