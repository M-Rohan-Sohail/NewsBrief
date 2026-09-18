import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base
from models import NewsCluster, UserPreference
from datetime import date, datetime, timezone
import uuid
import os

# Use a test database or sqlite if possible, but pgvector requires postgres.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/newsbrief_test")

@pytest.fixture(scope="module")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    try:
        # Create vector extension and tables
        with engine.begin() as conn:
            conn.execute(engine.dialect.statement_compiler.statement_cls("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(engine)
        yield engine
    except Exception as e:
        pytest.skip(f"Could not connect to postgres or setup vector: {e}")
    finally:
        try:
            Base.metadata.drop_all(engine)
        except:
            pass

@pytest.fixture(scope="function")
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

def test_pgvector_storage_and_cosine_distance(db_session):
    # Create two clusters with opposite embeddings
    cluster1 = NewsCluster(
        id=uuid.uuid4(),
        batch_date=date.today(),
        canonical_title="AI Research",
        representative_snippet="New model released.",
        source_count=1,
        matched_tags=["ai"],
        article_refs=[],
        embedding=[1.0] * 384
    )
    
    cluster2 = NewsCluster(
        id=uuid.uuid4(),
        batch_date=date.today(),
        canonical_title="Cooking Tips",
        representative_snippet="How to boil an egg.",
        source_count=1,
        matched_tags=["food"],
        article_refs=[],
        embedding=[-1.0] * 384 # Opposite vector
    )
    
    db_session.add_all([cluster1, cluster2])
    db_session.commit()
    
    # Query using cosine distance (<=>)
    query_vector = [1.0] * 384
    
    # Sort by cosine distance ascending (closest first)
    results = db_session.query(NewsCluster).order_by(
        NewsCluster.embedding.cosine_distance(query_vector)
    ).all()
    
    assert len(results) == 2
    assert results[0].id == cluster1.id, "Cluster 1 should be closest"
    assert results[1].id == cluster2.id, "Cluster 2 should be furthest"
