"""Tests du repository générique sur une base SQLite en mémoire (logique ORM indépendante de PostgreSQL)."""
from typing import Optional

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine

import models  # noqa: F401  (vérifie que l'import dynamique des modèles fonctionne)
from repositories.base_repository import BaseRepository


class ArticleTest(SQLModel, table=True):
    __tablename__ = "article_test_repository"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str = "divers"


@pytest.fixture
def repo():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    ArticleTest.__table__.create(engine)
    with Session(engine) as session:
        yield BaseRepository(ArticleTest, session)


def test_save_find_et_delete(repo):
    article = repo.save(ArticleTest(name="Riz 25 kg"))
    assert article.id is not None
    assert repo.findOne(article.id).name == "Riz 25 kg"
    assert repo.findOne(article.id, load_relations=True).name == "Riz 25 kg"
    assert repo.deleteOne(article.id) is True
    assert repo.deleteOne(article.id) is False


def test_insert_many_find_all_et_pagination(repo):
    repo.InsertMany([{"name": "A", "category": "x"}, {"name": "B", "category": "x"}, {"name": "C"}])
    repo.InsertMany([])
    assert len(repo.findAll()) == 3
    assert len(repo.findAll(limit=2)) == 2
    assert len(repo.findAll(limit=2, offset=2, load_relations=True)) == 1


def test_find_by_dynamique(repo):
    repo.InsertMany([{"name": "A", "category": "x"}, {"name": "B", "category": "y"}])
    assert [a.name for a in repo.findBy(category="x")] == ["A"]
    assert [a.name for a in repo.findByName("B")] == ["B"]
    assert len(repo.findBy(load_relations=True, champ_inconnu="z")) == 2
    with pytest.raises(AttributeError):
        repo.methodeInexistante()


def test_update_many_et_delete_many(repo):
    repo.InsertMany([{"name": "A", "category": "x"}, {"name": "B", "category": "x"}])
    assert repo.updateMany({"category": "x"}, {"category": "z"}) == 2
    assert repo.updateMany({"category": "z"}, {}) == 0
    ids = [a.id for a in repo.findAll()]
    assert repo.deleteMany(ids) == 2
    assert repo.deleteMany([]) == 0
