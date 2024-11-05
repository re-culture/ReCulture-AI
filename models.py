from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "User"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email}>"


class Profile(Base):
    __tablename__ = "Profile"
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey("User.id"), nullable=False)
    nickname = Column(String, nullable=False)
    profilePhoto = Column(String, nullable=False)
    bio = Column(String, nullable=True)
    birthdate = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Profile {self.id} {self.nickname} {self.userId}>"


class CulturePost(Base):
    __tablename__ = "CulturePost"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    emoji = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    categoryId = Column(Integer, nullable=False)
    authorId = Column(Integer, ForeignKey("User.id"), nullable=False)
    review = Column(String, nullable=False)
    disclosure = Column(String, nullable=False)
    detail1 = Column(String, nullable=True)
    detail2 = Column(String, nullable=True)
    detail3 = Column(String, nullable=True)
    detail4 = Column(String, nullable=True)
    createdAt = Column(DateTime, insert_default=datetime.now())
    updatedAt = Column(DateTime, default=datetime.now())

    def __repr__(self) -> str:
        return f"<CulturePost {self.id} {self.title} {self.emoji} {self.review}>"


class Photo(Base):
    __tablename__ = "Photo"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    culturePostId = Column(Integer, ForeignKey("CulturePost.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<Photo {self.url} {self.culturePostId}>"


class Bookmark(Base):
    __tablename__ = "Bookmark"
    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey("User.id"), nullable=False)
    postId = Column(Integer, ForeignKey("CulturePost.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<Bookmark {self.id} {self.userId} {self.postId}>"