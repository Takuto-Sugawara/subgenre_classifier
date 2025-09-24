#!/usr/bin/env python3
"""
Enhanced NCS Music Downloader with JSON Track Management
Automatically downloads music from NCS and manages track information in JSON format
Author: Assistant
Date: 2025-09-23

IMPORTANT: This script is for educational purposes only.
Please ensure you comply with NCS usage policy and terms of service.
Always provide proper attribution when using NCS music.
"""

import os
import time
import requests
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, date

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ncs_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Track:
    """Enhanced data class for track information"""
    title: str
    artists: List[str]
    genres: List[str]
    url: str
    download_url: Optional[str] = None
    publish_date: Optional[str] = None
    credit_info: Optional[str] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    track_id: Optional[str] = None

class TrackDatabase:
    """Manages track information in JSON format"""
    
    def __init__(self, db_path: str = "tracks_database.json"):
        self.db_path = Path(db_path)
        self.data = {"tracks": {}}
        self.load_database()
    
    def load_database(self):
        """Load existing database from file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    
                # Ensure proper structure
                if "tracks" not in self.data:
                    self.data["tracks"] = {}
                    
                logger.info(f"Loaded {len(self.data['tracks'])} tracks from database")
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                self.data = {"tracks": {}}
        else:
            logger.info("Creating new track database")
    
    def save_database(self):
        """Save database to file"""
        try:
            # Create backup
            if self.db_path.exists():
                backup_path = self.db_path.with_suffix('.backup.json')
                self.db_path.rename(backup_path)
            
            # Save current data
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
                
            logger.info(f"Database saved with {len(self.data['tracks'])} tracks")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def generate_track_id(self, track: Track) -> str:
        """Generate unique track ID"""
        # Create base ID from title
        base_id = re.sub(r'[^a-zA-Z0-9]', '_', track.title.lower())
        base_id = re.sub(r'_+', '_', base_id).strip('_')
        
        # Ensure uniqueness
        track_id = base_id
        counter = 1
        while f"track_{track_id}" in self.data["tracks"]:
            track_id = f"{base_id}_{counter}"
            counter += 1
        
        return f"track_{track_id}"
    
    def add_track(self, track: Track) -> str:
        """Add track to database and return track ID"""
        track_id = self.generate_track_id(track)
        track.track_id = track_id
        
        track_data = {
            "title": track.title,
            "genres": track.genres,
            "artists": track.artists,
            "url": track.download_url or track.url,
            "publish_date": track.publish_date,
            "original_url": track.url,
            "credit_info": track.credit_info,
            "file_path": track.file_path,
            "file_size": track.file_size,
            "download_timestamp": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        self.data["tracks"][track_id] = track_data
        logger.info(f"Added track to database: {track_id}")
        return track_id
    
    def update_track(self, track_id: str, track: Track):
        """Update existing track in database"""
        if track_id in self.data["tracks"]:
            self.data["tracks"][track_id].update({
                "title": track.title,
                "genres": track.genres,
                "artists": track.artists,
                "url": track.download_url or track.url,
                "publish_date": track.publish_date,
                "credit_info": track.credit_info,
                "file_path": track.file_path,
                "file_size": track.file_size,
                "last_updated": datetime.now().isoformat()
            })
            logger.info(f"Updated track in database: {track_id}")
    
    def track_exists(self, track: Track) -> Optional[str]:
        """Check if track already exists in database"""
        for track_id, track_data in self.data["tracks"].items():
            if (track_data["title"].lower() == track.title.lower() and 
                track_data.get("original_url") == track.url):
                return track_id
        return None
    
    def get_stats(self) -> Dict[str, any]:
        """Get database statistics"""
        tracks = self.data["tracks"]
        
        # Count by genre
        genre_counts = {}
        for track_data in tracks.values():
            for genre in track_data.get("genres", []):
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Count by artist
        artist_counts = {}
        for track_data in tracks.values():
            for artist in track_data.get("artists", []):
                artist_counts[artist] = artist_counts.get(artist, 0) + 1
        
        # Calculate total file size
        total_size = sum(track_data.get("file_size", 0) for track_data in tracks.values())
        
        return {
            "total_tracks": len(tracks),
            "total_file_size": total_size,
            "total_file_size_mb": round(total_size / (1024 * 1024), 2),
            "genres": dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)),
            "artists": dict(sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)),
            "most_recent_download": max([t.get("download_timestamp", "") for t in tracks.values()] or [""])
        }

class EnhancedNCSDownloader:
    """Enhanced NCS downloader with JSON track management"""
    
    def __init__(self, download_dir: str = "ncs_downloads", delay: float = 2.0, dry_run: bool = False):
        """Initialize the enhanced NCS downloader"""
        self.base_url = "https://ncs.io"
        self.download_dir = Path(download_dir)
        self.delay = delay
        self.dry_run = dry_run
        self.driver = None
        self.session = requests.Session()
        self.discovered_urls: Set[str] = set()
        
        # Initialize track database
        self.db = TrackDatabase(self.download_dir / "tracks_database.json")
        
        # Create download directory
        if not self.dry_run:
            self.download_dir.mkdir(exist_ok=True)
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        logger.info(f"Enhanced NCS Downloader initialized. Download directory: {self.download_dir}")
        if self.dry_run:
            logger.info("Running in DRY RUN mode - no files will be downloaded")

    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            logger.info("Chrome WebDriver initialized successfully")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def extract_track_metadata(self, soup: BeautifulSoup, url: str) -> Track:
        """Extract comprehensive track metadata from page"""
        track = Track(
            title="Unknown Title",
            artists=["Unknown Artist"],
            genres=[],
            url=url
        )
        
        # Extract title
        title_selectors = [
            'h1',
            '[class*="title"]',
            '[class*="track"]',
            'meta[property="og:title"]',
            'title'
        ]
        
        for selector in title_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    track.title = element.get('content').strip()
                    break
            else:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    title = element.get_text(strip=True)
                    # Clean title from common patterns
                    title = re.sub(r'\[.*?\]', '', title).strip()
                    if title and len(title) > 3:
                        track.title = title
                        break
        
        # Extract artists
        artist_selectors = [
            '[class*="artist"]',
            '[class*="by"]',
            'meta[name="author"]',
            'h2', 'h3'
        ]
        
        artists_found = []
        for selector in artist_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    artists_found.extend(self.parse_artists(element.get('content')))
                    break
            else:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and ('by' in text.lower() or len(text.split()) <= 4):
                        artists_found.extend(self.parse_artists(text))
        
        if artists_found:
            track.artists = list(set(artists_found))  # Remove duplicates
        
        # Extract genres/tags
        genre_selectors = [
            '[class*="genre"]',
            '[class*="tag"]',
            '[class*="category"]',
            'meta[name="keywords"]'
        ]
        
        genres_found = []
        for selector in genre_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    genres_found.extend(self.parse_genres(element.get('content')))
            else:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text:
                        genres_found.extend(self.parse_genres(text))
        
        # Add default Electronic genre if none found
        if not genres_found:
            genres_found = ["Electronic"]
        
        track.genres = list(set(genres_found))
        
        # Extract publish date
        date_selectors = [
            '[class*="date"]',
            '[class*="published"]',
            'time',
            'meta[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    track.publish_date = self.parse_date(element.get('content'))
                    break
            else:
                element = soup.select_one(selector)
                if element:
                    # Check for datetime attribute
                    datetime_attr = element.get('datetime')
                    if datetime_attr:
                        track.publish_date = self.parse_date(datetime_attr)
                        break
                    
                    # Check text content
                    text = element.get_text(strip=True)
                    if text:
                        parsed_date = self.parse_date(text)
                        if parsed_date:
                            track.publish_date = parsed_date
                            break
        
        # Extract credit info
        credit_selectors = [
            '[class*="credit"]',
            '[class*="attribution"]',
            'p:contains("Music provided by")',
            'p:contains("NCS")'
        ]
        
        for selector in credit_selectors:
            if ':contains(' in selector:
                # Handle BeautifulSoup limitation with :contains
                elements = soup.find_all('p')
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if 'Music provided by' in text or 'NCS' in text:
                        track.credit_info = text
                        break
            else:
                element = soup.select_one(selector)
                if element:
                    track.credit_info = element.get_text(strip=True)
                    break
        
        logger.info(f"Extracted metadata - Title: {track.title}, Artists: {track.artists}, Genres: {track.genres}")
        return track

    def parse_artists(self, text: str) -> List[str]:
        """Parse artist names from text"""
        if not text:
            return []
        
        # Clean common prefixes
        text = re.sub(r'^(by|artist:?)\s*', '', text, flags=re.IGNORECASE)
        
        # Split by common separators
        separators = [' feat. ', ' ft. ', ' & ', ' and ', ',', ' x ', ' X ']
        artists = [text]
        
        for sep in separators:
            new_artists = []
            for artist in artists:
                new_artists.extend([a.strip() for a in artist.split(sep)])
            artists = new_artists
        
        # Filter and clean
        cleaned_artists = []
        for artist in artists:
            artist = artist.strip()
            if artist and len(artist) > 1 and not artist.lower() in ['the', 'a', 'an']:
                cleaned_artists.append(artist)
        
        return cleaned_artists[:5]  # Limit to 5 artists maximum

    def parse_genres(self, text: str) -> List[str]:
        """Parse genre names from text"""
        if not text:
            return []
        
        # Common electronic music genres
        known_genres = [
            'House', 'Progressive House', 'Deep House', 'Tech House',
            'Dubstep', 'Drum & Bass', 'DnB', 'Trap', 'Future Bass',
            'Electro', 'Electronic', 'EDM', 'Ambient', 'Chill',
            'Synthwave', 'Melodic Dubstep', 'Hardstyle', 'Trance'
        ]
        
        text_lower = text.lower()
        found_genres = []
        
        for genre in known_genres:
            if genre.lower() in text_lower:
                found_genres.append(genre)
        
        # If no known genres found, try to extract from tags
        if not found_genres:
            # Split by common separators and capitalize
            tags = re.split(r'[,;&|]', text)
            for tag in tags:
                tag = tag.strip().title()
                if tag and len(tag) > 2:
                    found_genres.append(tag)
        
        return found_genres[:3]  # Limit to 3 genres maximum

    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%d %B %Y'
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.split('T')[0], fmt.split('T')[0])
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try to extract year at least
        year_match = re.search(r'20\d{2}', date_str)
        if year_match:
            return f"{year_match.group()}-01-01"
        
        return None

    def get_track_details_enhanced(self, track: Track) -> Track:
        """Get enhanced track details with comprehensive metadata extraction"""
        if not self.driver:
            self.driver = self.setup_driver()
        
        try:
            logger.info(f"Getting enhanced details for track: {track.url}")
            self.driver.get(track.url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(self.delay)
            
            # Parse page content
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract comprehensive metadata
            enhanced_track = self.extract_track_metadata(soup, track.url)
            
            # Find download URL
            download_url = None
            download_selectors = [
                "a[href*='.mp3']",
                "a[download]",
                "*[class*='download'] a",
                "button[onclick*='download']",
                "a[href*='download']"
            ]
            
            for selector in download_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    href = element.get_attribute('href')
                    if href and ('.mp3' in href or 'download' in href.lower()):
                        download_url = href
                        logger.info(f"Found download URL using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            enhanced_track.download_url = download_url
            
            logger.info(f"Enhanced track details: {enhanced_track.title} by {enhanced_track.artists}")
            
        except Exception as e:
            logger.error(f"Error getting enhanced track details for {track.url}: {e}")
            enhanced_track = track  # Return original if enhancement fails
        
        return enhanced_track

    def download_track_with_database(self, track: Track) -> bool:
        """Download track and update database"""
        # Check if track already exists in database
        existing_id = self.db.track_exists(track)
        if existing_id:
            logger.info(f"Track already exists in database: {existing_id}")
            return True
        
        if not track.download_url:
            logger.warning(f"No download URL for track: {track.title}")
            return False
        
        try:
            # Create safe filename
            artist_str = "_".join(track.artists[:2]) if track.artists else "Unknown"
            safe_filename = self.sanitize_filename(f"{artist_str} - {track.title}.mp3")
            file_path = self.download_dir / safe_filename
            
            # Skip if file already exists
            if file_path.exists() and not self.dry_run:
                logger.info(f"File already exists: {safe_filename}")
                track.file_path = str(file_path)
                track.file_size = file_path.stat().st_size
                self.db.add_track(track)
                self.db.save_database()
                return True
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would download {safe_filename} from {track.download_url}")
                track.file_path = str(file_path)
                self.db.add_track(track)
                self.db.save_database()
                return True
            
            logger.info(f"Downloading: {safe_filename}")
            
            # Validate download URL first
            if not self.validate_download_url(track.download_url):
                logger.warning(f"Invalid download URL: {track.download_url}")
                return False
            
            # Download file
            response = self.session.get(track.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
            
            # Verify file
            if file_path.stat().st_size == 0:
                file_path.unlink()
                logger.error(f"Downloaded file is empty: {safe_filename}")
                return False
            
            # Update track info
            track.file_path = str(file_path)
            track.file_size = file_path.stat().st_size
            
            # Add to database
            track_id = self.db.add_track(track)
            self.db.save_database()
            
            logger.info(f"Successfully downloaded and added to database: {safe_filename} ({track_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading track {track.title}: {e}")
            if 'file_path' in locals() and file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            return False

    def validate_download_url(self, url: str) -> bool:
        """Validate download URL"""
        try:
            response = self.session.head(url, timeout=10)
            content_type = response.headers.get('content-type', '').lower()
            
            audio_types = ['audio/', 'application/octet-stream']
            is_audio = any(audio_type in content_type for audio_type in audio_types)
            has_audio_ext = url.lower().endswith(('.mp3', '.wav', '.flac', '.m4a'))
            
            return response.status_code == 200 and (is_audio or has_audio_ext)
            
        except Exception as e:
            logger.warning(f"Could not validate download URL {url}: {e}")
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        filename = re.sub(r'[_\s]+', '_', filename)
        
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename

    def discover_tracks_sample(self) -> List[Track]:
        """Discover sample tracks for testing - replace with actual discovery logic"""
        sample_tracks = [
            Track(title="Fade", artists=["Alan Walker"], genres=["Progressive House"], url="https://ncs.io/fade"),
            Track(title="Spectre", artists=["Alan Walker"], genres=["Electronic"], url="https://ncs.io/spectre"),
            Track(title="Cradles", artists=["Sub Urban"], genres=["Dark Electronic"], url="https://ncs.io/cradles")
        ]
        
        logger.info(f"Discovered {len(sample_tracks)} sample tracks")
        return sample_tracks

    def download_all_enhanced(self, limit: Optional[int] = None) -> Dict[str, any]:
        """Download all tracks with enhanced database management"""
        stats = {
            'total': 0, 'success': 0, 'failed': 0, 'skipped': 0, 
            'already_in_db': 0, 'invalid_urls': 0
        }
        
        try:
            # Discover tracks - replace with actual discovery method
            tracks = self.discover_tracks_sample()
            
            if limit:
                tracks = tracks[:limit]
            
            stats['total'] = len(tracks)
            logger.info(f"Starting enhanced download of {len(tracks)} tracks...")
            
            for i, track in enumerate(tracks, 1):
                logger.info(f"Processing track {i}/{len(tracks)}: {track.title}")
                
                try:
                    # Check if already in database
                    if self.db.track_exists(track):
                        stats['already_in_db'] += 1
                        logger.info(f"Track already in database: {track.title}")
                        continue
                    
                    # Get enhanced track details
                    track = self.get_track_details_enhanced(track)
                    
                    if not track.download_url:
                        stats['invalid_urls'] += 1
                        continue
                    
                    # Download and add to database
                    if self.download_track_with_database(track):
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing track {track.title}: {e}")
                    stats['failed'] += 1
                
                time.sleep(self.delay)
            
            # Final database save and stats
            self.db.save_database()
            db_stats = self.db.get_stats()
            stats.update({'database_stats': db_stats})
            
            logger.info(f"Enhanced download completed. Stats: {stats}")
            
        except Exception as e:
            logger.error(f"Error during enhanced bulk download: {e}")
        finally:
            self.cleanup()
        
        return stats

    def export_database(self, format_type: str = "json") -> str:
        """Export database in various formats"""
        if format_type == "json":
            export_path = self.download_dir / "tracks_export.json"
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.db.data, f, indent=4, ensure_ascii=False)
        
        elif format_type == "csv":
            import csv
            export_path = self.download_dir / "tracks_export.csv"
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Track ID', 'Title', 'Artists', 'Genres', 'URL', 'Publish Date', 'File Path'])
                
                for track_id, track_data in self.db.data["tracks"].items():
                    writer.writerow([
                        track_id,
                        track_data.get('title', ''),
                        '; '.join(track_data.get('artists', [])),
                        '; '.join(track_data.get('genres', [])),
                        track_data.get('url', ''),
                        track_data.get('publish_date', ''),
                        track_data.get('file_path', '')
                    ])
        
        logger.info(f"Database exported to: {export_path}")
        return str(export_path)

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        logger.info("Resources cleaned up")

def main():
    """Main function with enhanced database features"""
    print("Enhanced NCS Music Downloader with JSON Database")
    print("=" * 60)
    print("IMPORTANT: Please ensure you comply with NCS usage policy.")
    print("Always provide proper attribution when using NCS music.")
    print("=" * 60)
    
    print("\nOptions:")
    print("1. Download tracks with database management")
    print("2. View database statistics")
    print("3. Export database")
    print("4. Test single track with metadata extraction")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    download_dir = input("Enter download directory (default: ncs_downloads): ").strip() or "ncs_downloads"
    
    if choice == "2":
        # View database stats
        downloader = EnhancedNCSDownloader(download_dir=download_dir, dry_run=True)
        stats = downloader.db.get_stats()
        print("\nDatabase Statistics:")
        print(json.dumps(stats, indent=2))
        return
    
    elif choice == "3":
        # Export database
        downloader = EnhancedNCSDownloader(download_dir=download_dir, dry_run=True)
        format_type = input("Export format (json/csv, default: json): ").strip() or "json"
        export_path = downloader.export_database(format_type)
        print(f"Database exported to: {export_path}")
        return
    
    elif choice == "4":
        # Test single track
        track_url = input("Enter track URL: ").strip()
        downloader = EnhancedNCSDownloader(download_dir=download_dir, dry_run=True)
        
        test_track = Track(title="Test", artists=["Test"], genres=[], url=track_url)
        enhanced_track = downloader.get_track_details_enhanced(test_track)
        
        print("\nExtracted Metadata:")
        print(f"Title: {enhanced_track.title}")
        print(f"Artists: {enhanced_track.artists}")
        print(f"Genres: {enhanced_track.genres}")
        print(f"Publish Date: {enhanced_track.publish_date}")
        print(f"Download URL: {enhanced_track.download_url}")
        print(f"Credit Info: {enhanced_track.credit_info}")
        downloader.cleanup()
        return
    
    # Main download process
    dry_run = input("Run in dry mode? (y/n, default: n): ").strip().lower() == 'y'
    
    limit = None
    if choice == "1":
        try:
            limit_input = input("Enter max tracks to download (default: all): ").strip()
            limit = int(limit_input) if limit_input else None
        except ValueError:
            print("Invalid number, downloading all tracks")
            limit = None
    
    # Initialize enhanced downloader
    downloader = EnhancedNCSDownloader(download_dir=download_dir, delay=2.0, dry_run=dry_run)
    
    try:
        # Start enhanced download process
        stats = downloader.download_all_enhanced(limit=limit)
        
        print("\nDownload Summary:")
        print("=" * 40)
        print(f"Total tracks processed: {stats['total']}")
        print(f"Successfully downloaded: {stats['success']}")
        print(f"Failed downloads: {stats['failed']}")
        print(f"Already in database: {stats['already_in_db']}")
        print(f"Invalid URLs: {stats['invalid_urls']}")
        print(f"Skipped: {stats['skipped']}")
        
        if 'database_stats' in stats:
            db_stats = stats['database_stats']
            print("\nDatabase Statistics:")
            print("=" * 40)
            print(f"Total tracks in database: {db_stats['total_tracks']}")
            print(f"Total file size: {db_stats['total_file_size_mb']} MB")
            
            if db_stats['genres']:
                print(f"\nTop genres:")
                for genre, count in list(db_stats['genres'].items())[:5]:
                    print(f"  {genre}: {count} tracks")
            
            if db_stats['artists']:
                print(f"\nTop artists:")
                for artist, count in list(db_stats['artists'].items())[:5]:
                    print(f"  {artist}: {count} tracks")
        
        if dry_run:
            print("\nThis was a dry run. Run again without dry mode to download files.")
        else:
            print(f"\nDatabase saved to: {downloader.db.db_path}")
            print("Use option 2 to view detailed database statistics.")
            print("Use option 3 to export database in different formats.")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        downloader.db.save_database()  # Save database even if interrupted
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        downloader.db.save_database()  # Save database on error
    finally:
        downloader.cleanup()

if __name__ == "__main__":
    main()