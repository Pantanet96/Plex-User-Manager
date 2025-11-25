from plexapi.server import PlexServer
from database import db
from models import PlexUser, Library, Share, Settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_plex_server():
    url_setting = Settings.query.filter_by(key='plex_url').first()
    token_setting = Settings.query.filter_by(key='plex_token').first()
    
    if not url_setting or not token_setting:
        return None
        
    import requests
    session = requests.Session()
    session.verify = False
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    return PlexServer(url_setting.value, token_setting.value, session=session)

def sync_plex_data():
    logger.info("Starting Plex sync...")
    try:
        plex = get_plex_server()
        if not plex:
            logger.error("Plex credentials not configured.")
            return False, "Plex credentials not configured."
        
        logger.info(f"Connected to Plex server: {plex.friendlyName}")

        # Sync Libraries
        plex_libraries = plex.library.sections()
        logger.info(f"Found {len(plex_libraries)} libraries.")
        for lib in plex_libraries:
            existing_lib = Library.query.filter_by(plex_key=str(lib.key)).first()
            if not existing_lib:
                new_lib = Library(plex_key=str(lib.key), title=lib.title, type=lib.type)
                db.session.add(new_lib)
                logger.info(f"Added new library: {lib.title}")
            else:
                existing_lib.title = lib.title
        
        # Sync Users (Friends/Shared Users)
        # plex.myPlexAccount().users() returns users you share with
        account = plex.myPlexAccount()
        plex_users = account.users()
        logger.info(f"Found {len(plex_users)} users.")
        
        for user in plex_users:
            existing_user = PlexUser.query.filter_by(plex_id=str(user.id)).first()
            if not existing_user:
                new_user = PlexUser(
                    plex_id=str(user.id),
                    username=user.title, # username is often in title or username
                    email=user.email,
                    thumb=user.thumb
                )
                db.session.add(new_user)
                db.session.flush() # Flush to get ID
                current_db_user = new_user
                logger.info(f"Added new user: {user.title}")
            else:
                existing_user.username = user.title
                existing_user.email = user.email
                existing_user.thumb = user.thumb
                current_db_user = existing_user

            # Sync existing shares
            # We need to find what this server shares with this user
            # user.servers is a list of servers shared with this user?
            # Or we need to ask the server for the list of shared sections for this user.
            
            # According to plexapi docs/source:
            # account.users() returns User objects.
            # User objects have a 'servers' attribute which lists servers shared with them?
            # Or we use plex.myPlexAccount().user(user.title).servers?
            
            # Let's try to get the specific server share info
            # The 'user' object from account.users() might already have it.
            # user.servers is a list of SharedServer objects.
            
            # We need to match the machineIdentifier of our server
            my_machine_id = plex.machineIdentifier
            
            for shared_server in user.servers:
                if shared_server.machineIdentifier == my_machine_id:
                    # This is our server shared with this user
                    # shared_server.sections() returns the sections shared
                    # But wait, shared_server might not have sections() method directly if it's a SharedServer object
                    # It might have 'sections' attribute which is a list of SharedSection
                    
                    # Let's assume shared_server.sections is a list of objects with 'key' or 'id'
                    # Actually, looking at plexapi, it seems we might need to iterate sections
                    
                    if hasattr(shared_server, 'sections'):
                        # If sections is a list of objects or method
                        sections = shared_server.sections
                        if callable(sections):
                            sections = sections()
                            
                        for section in sections:
                            # section.key should match library.plex_key
                            # Note: section.key might be the section ID
                            
                            lib = Library.query.filter_by(plex_key=str(section.key)).first()
                            if lib:
                                # Create or update Share
                                share = Share.query.filter_by(plex_user_id=current_db_user.id, library_id=lib.id).first()
                                if not share:
                                    share = Share(plex_user_id=current_db_user.id, library_id=lib.id, is_active=True)
                                    db.session.add(share)
                                    logger.info(f"Imported existing share: {lib.title} for {user.title}")
                                else:
                                    # Ensure it's active if it exists on Plex
                                    share.is_active = True
                    break
        
        db.session.commit()
        logger.info("Sync completed successfully.")
        return True, "Sync successful."
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        return False, str(e)

def update_user_access(plex_user_id, library_keys):
    logger.info(f"Updating access for user {plex_user_id} with libraries: {library_keys}")
    
    # If user has no libraries assigned, skip the update entirely
    if not library_keys:
        logger.info("User has no libraries assigned - skipping Plex update")
        return True, "No libraries to share - user not invited."
    
    try:
        plex = get_plex_server()
        if not plex:
            logger.error("Plex credentials not configured.")
            return False, "Plex credentials not configured."
        
        account = plex.myPlexAccount()
        user = account.user(plex_user_id)
        logger.info(f"Found user: {user.title} (email: {user.email})")
        
        sections_to_share = []
        for key in library_keys:
            for section in plex.library.sections():
                if str(section.key) == str(key):
                    sections_to_share.append(section)
                    break
        
        # Only add "Default" library if user has at least one library assigned
        # This prevents user removal from server when modifying shares
        default_lib = None
        for section in plex.library.sections():
            if section.title.lower() == 'default':
                default_lib = section
                # Check if it's not already in the list
                if not any(s.key == section.key for s in sections_to_share):
                    sections_to_share.append(section)
                    logger.info("Added 'Default' library automatically to prevent user removal")
                break
        
        if not default_lib:
            logger.warning("'Default' library not found on Plex server!")

        
        logger.info(f"Sections to share: {[s.title for s in sections_to_share]}")
        
        # Simply pass the desired sections - plexapi should handle the diff
        logger.info(f"Calling account.updateFriend with {len(sections_to_share)} sections")
        account.updateFriend(user=user, server=plex, sections=sections_to_share)
        
        logger.info("Access updated successfully.")
        return True, "Access updated successfully."
    except Exception as e:
        logger.error(f"Update failed: {str(e)}")
        return False, str(e)


def check_schedules():
    """
    Background job to check for expired or starting shares.
    """
    # To avoid circular imports, we'll implement the logic here but need to ensure
    # it's called within an app context in app.py
    
    users = PlexUser.query.all()
    now = datetime.now()
    
    for user in users:
        active_library_keys = []
        shares = Share.query.filter_by(plex_user_id=user.id).all()
        
        needs_update = False
        
        for share in shares:
            if share.is_active:
                should_share = True
                if share.start_date and share.start_date > now:
                    should_share = False
                if share.expiration_date and share.expiration_date <= now:
                    should_share = False
                
                if should_share:
                    active_library_keys.append(share.library.plex_key)
        
        # Update Plex for this user
        try:
            update_user_access(user.plex_id, active_library_keys)
            print(f"Updated access for user {user.username}")
        except Exception as e:
            print(f"Failed to update access for user {user.username}: {e}")

