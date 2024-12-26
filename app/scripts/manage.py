import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import click
import json
from datetime import datetime, UTC, timedelta
from sqlalchemy import func
from app.scripts.create_superuser import create_superuser
from app.db.session import SessionLocal
from app.models import User, Topic, Session, UserAnalytics
from app.core.security import get_password_hash

@click.group()
def cli():
    """Management script for the AI Tutor application."""
    pass

@cli.command()
def createsuperuser():
    """Create a superuser if it doesn't exist."""
    db = SessionLocal()
    try:
        create_superuser(db)
    finally:
        db.close()

@cli.command()
@click.argument('email')
@click.option('--active/--inactive', default=True, help="Set user active status")
def manage_user(email: str, active: bool):
    """Manage user status (activate/deactivate)."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User {email} not found")
            return
        
        user.is_active = active
        db.commit()
        status = "activated" if active else "deactivated"
        click.echo(f"✅ User {email} has been {status}")
    finally:
        db.close()

@cli.command()
@click.argument('days', type=int, default=30)
def cleanup_inactive(days: int):
    """Clean up inactive sessions older than specified days."""
    db = SessionLocal()
    try:
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        
        # Delete old sessions
        deleted_sessions = db.query(Session).filter(
            Session.created_at < cutoff_date,
            Session.completion_rate == 0
        ).delete()
        
        # Clean up analytics
        deleted_analytics = db.query(UserAnalytics).filter(
            UserAnalytics.created_at < cutoff_date,
            ~UserAnalytics.user_id.in_(
                db.query(Session.user_id).distinct()
            )
        ).delete()
        
        db.commit()
        click.echo(f"✅ Cleaned up {deleted_sessions} inactive sessions")
        click.echo(f"✅ Cleaned up {deleted_analytics} stale analytics records")
    finally:
        db.close()

@cli.command()
@click.argument('output_file', type=click.Path())
def export_topics(output_file: str):
    """Export all topics to a JSON file."""
    db = SessionLocal()
    try:
        topics = db.query(Topic).all()
        
        # Convert topics to dict
        topics_data = []
        for topic in topics:
            topic_dict = {
                "id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "content": topic.content,
                "difficulty_level": topic.difficulty_level,
                "parent_id": topic.parent_id,
                "engagement_score": topic.engagement_score
            }
            topics_data.append(topic_dict)
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(topics_data, f, indent=2)
        
        click.echo(f"✅ Exported {len(topics_data)} topics to {output_file}")
    finally:
        db.close()

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--update/--no-update', default=False, 
              help="Update existing topics if they exist")
def import_topics(input_file: str, update: bool):
    """Import topics from a JSON file."""
    db = SessionLocal()
    try:
        with open(input_file, 'r') as f:
            topics_data = json.load(f)
        
        created = 0
        updated = 0
        skipped = 0
        
        for topic_data in topics_data:
            existing = db.query(Topic).filter(Topic.id == topic_data['id']).first()
            
            if existing and not update:
                skipped += 1
                continue
            
            if existing and update:
                for key, value in topic_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                topic = Topic(**topic_data)
                db.add(topic)
                created += 1
        
        db.commit()
        click.echo(f"✅ Created {created} topics")
        click.echo(f"✅ Updated {updated} topics")
        click.echo(f"ℹ️  Skipped {skipped} existing topics")
    finally:
        db.close()

@cli.command()
def show_stats():
    """Show system statistics."""
    db = SessionLocal()
    try:
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        total_topics = db.query(func.count(Topic.id)).scalar()
        total_sessions = db.query(func.count(Session.id)).scalar()
        avg_completion = db.query(func.avg(Session.completion_rate)).scalar() or 0
        
        click.echo("\n📊 System Statistics")
        click.echo("================")
        click.echo(f"Total Users: {total_users}")
        click.echo(f"Active Users: {active_users}")
        click.echo(f"Total Topics: {total_topics}")
        click.echo(f"Total Sessions: {total_sessions}")
        click.echo(f"Average Completion Rate: {avg_completion:.2%}")
    finally:
        db.close()

if __name__ == "__main__":
    cli() 