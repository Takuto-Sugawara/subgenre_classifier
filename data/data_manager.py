#!/usr/bin/env python3
"""
Database Management Utilities for NCS Downloader
Provides tools for database management, search, and analysis
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import argparse

class DatabaseManager:
    """Advanced database management for NCS tracks"""
    
    def __init__(self, db_path: str = "ncs_downloads/tracks_database.json"):
        self.db_path = Path(db_path)
        self.data = {"tracks": {}}
        self.load_database()
    
    def load_database(self):
        """Load database from file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"Loaded {len(self.data.get('tracks', {}))} tracks from database")
            except Exception as e:
                print(f"Error loading database: {e}")
                self.data = {"tracks": {}}
        else:
            print(f"Database not found: {self.db_path}")
    
    def search_tracks(self, query: str, field: str = "all") -> List[Dict[str, Any]]:
        """
        Search tracks in database
        
        Args:
            query: Search query
            field: Field to search in (title, artist, genre, all)
        """
        results = []
        query_lower = query.lower()
        
        for track_id, track_data in self.data["tracks"].items():
            match = False
            
            if field == "all" or field == "title":
                if query_lower in track_data.get("title", "").lower():
                    match = True
            
            if field == "all" or field == "artist":
                artists = track_data.get("artists", [])
                if any(query_lower in artist.lower() for artist in artists):
                    match = True
            
            if field == "all" or field == "genre":
                genres = track_data.get("genres", [])
                if any(query_lower in genre.lower() for genre in genres):
                    match = True
            
            if match:
                result = track_data.copy()
                result["track_id"] = track_id
                results.append(result)
        
        return results
    
    def get_tracks_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Get all tracks of a specific genre"""
        return self.search_tracks(genre, "genre")
    
    def get_tracks_by_artist(self, artist: str) -> List[Dict[str, Any]]:
        """Get all tracks by a specific artist"""
        return self.search_tracks(artist, "artist")
    
    def get_tracks_by_year(self, year: str) -> List[Dict[str, Any]]:
        """Get all tracks published in a specific year"""
        results = []
        
        for track_id, track_data in self.data["tracks"].items():
            publish_date = track_data.get("publish_date", "")
            if publish_date.startswith(year):
                result = track_data.copy()
                result["track_id"] = track_id
                results.append(result)
        
        return results
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        tracks = self.data["tracks"]
        
        if not tracks:
            return {"error": "No tracks in database"}
        
        # Basic counts
        total_tracks = len(tracks)
        
        # File size analysis
        file_sizes = [t.get("file_size", 0) for t in tracks.values()]
        total_size = sum(file_sizes)
        avg_size = total_size / len(file_sizes) if file_sizes else 0
        
        # Genre analysis
        genre_counts = {}
        for track_data in tracks.values():
            for genre in track_data.get("genres", []):
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Artist analysis
        artist_counts = {}
        for track_data in tracks.values():
            for artist in track_data.get("artists", []):
                artist_counts[artist] = artist_counts.get(artist, 0) + 1
        
        # Year analysis
        year_counts = {}
        for track_data in tracks.values():
            publish_date = track_data.get("publish_date", "")
            if publish_date:
                year = publish_date[:4]
                year_counts[year] = year_counts.get(year, 0) + 1
        
        # Download timeline
        download_dates = []
        for track_data in tracks.values():
            download_timestamp = track_data.get("download_timestamp")
            if download_timestamp:
                try:
                    date = datetime.fromisoformat(download_timestamp.replace('Z', '+00:00'))
                    download_dates.append(date.strftime('%Y-%m-%d'))
                except:
                    continue
        
        download_date_counts = {}
        for date in download_dates:
            download_date_counts[date] = download_date_counts.get(date, 0) + 1
        
        return {
            "total_tracks": total_tracks,
            "total_file_size_bytes": total_size,
            "total_file_size_mb": round(total_size / (1024 * 1024), 2),
            "total_file_size_gb": round(total_size / (1024 * 1024 * 1024), 3),
            "average_file_size_mb": round(avg_size / (1024 * 1024), 2),
            "genres": {
                "total_unique": len(genre_counts),
                "counts": dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
            },
            "artists": {
                "total_unique": len(artist_counts),
                "counts": dict(sorted(artist_counts.items(), key=lambda x: x[1], reverse=True))
            },
            "years": {
                "total_unique": len(year_counts),
                "counts": dict(sorted(year_counts.items(), key=lambda x: x[1], reverse=True))
            },
            "download_timeline": dict(sorted(download_date_counts.items()))
        }
    
    def export_playlist(self, tracks: List[Dict], format_type: str = "m3u") -> str:
        """Export tracks as playlist"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "m3u":
            playlist_path = self.db_path.parent / f"ncs_playlist_{timestamp}.m3u"
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for track in tracks:
                    file_path = track.get("file_path", "")
                    if file_path and Path(file_path).exists():
                        title = track.get("title", "Unknown")
                        artists = ", ".join(track.get("artists", ["Unknown"]))
                        f.write(f"#EXTINF:-1,{artists} - {title}\n")
                        f.write(f"{file_path}\n")
        
        elif format_type == "json":
            playlist_path = self.db_path.parent / f"ncs_playlist_{timestamp}.json"
            
            playlist_data = {
                "name": f"NCS Playlist {timestamp}",
                "created": datetime.now().isoformat(),
                "tracks": tracks
            }
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
        
        print(f"Playlist exported to: {playlist_path}")
        return str(playlist_path)
    
    def cleanup_database(self) -> Dict[str, int]:
        """Clean up database by removing entries with missing files"""
        stats = {"total": 0, "missing_files": 0, "removed": 0}
        
        tracks_to_remove = []
        
        for track_id, track_data in self.data["tracks"].items():
            stats["total"] += 1
            file_path = track_data.get("file_path")
            
            if file_path:
                if not Path(file_path).exists():
                    stats["missing_files"] += 1
                    tracks_to_remove.append(track_id)
        
        # Remove tracks with missing files
        for track_id in tracks_to_remove:
            del self.data["tracks"][track_id]
            stats["removed"] += 1
        
        # Save cleaned database
        if stats["removed"] > 0:
            self.save_database()
            print(f"Removed {stats['removed']} tracks with missing files")
        
        return stats
    
    def save_database(self):
        """Save database to file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            print(f"Database saved to: {self.db_path}")
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive database report"""
        stats = self.get_detailed_stats()
        
        if "error" in stats:
            return stats["error"]
        
        report_lines = [
            "NCS Music Database Report",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "OVERVIEW",
            "-" * 20,
            f"Total tracks: {stats['total_tracks']}",
            f"Total file size: {stats['total_file_size_gb']} GB ({stats['total_file_size_mb']} MB)",
            f"Average file size: {stats['average_file_size_mb']} MB",
            "",
            "GENRES",
            "-" * 20,
            f"Unique genres: {stats['genres']['total_unique']}",
        ]
        
        # Top 10 genres
        for genre, count in list(stats["genres"]["counts"].items())[:10]:
            report_lines.append(f"  {genre}: {count} tracks")
        
        report_lines.extend([
            "",
            "ARTISTS",
            "-" * 20,
            f"Unique artists: {stats['artists']['total_unique']}",
        ])
        
        # Top 10 artists
        for artist, count in list(stats["artists"]["counts"].items())[:10]:
            report_lines.append(f"  {artist}: {count} tracks")
        
        report_lines.extend([
            "",
            "YEARS",
            "-" * 20,
        ])
        
        # Years distribution
        for year, count in stats["years"]["counts"].items():
            report_lines.append(f"  {year}: {count} tracks")
        
        report_lines.extend([
            "",
            "DOWNLOAD TIMELINE",
            "-" * 20,
        ])
        
        # Recent downloads
        recent_downloads = list(stats["download_timeline"].items())[-10:]
        for date, count in recent_downloads:
            report_lines.append(f"  {date}: {count} tracks")
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"Report saved to: {output_file}")
        
        return report_content

def main():
    """Main CLI interface for database utilities"""
    parser = argparse.ArgumentParser(description="NCS Database Management Utilities")
    parser.add_argument("--db", default="ncs_downloads/tracks_database.json", 
                       help="Path to database file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search tracks")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--field", choices=["all", "title", "artist", "genre"], 
                              default="all", help="Field to search in")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export database")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json",
                              help="Export format")
    
    # Playlist command
    playlist_parser = subparsers.add_parser("playlist", help="Create playlist")
    playlist_parser.add_argument("--genre", help="Filter by genre")
    playlist_parser.add_argument("--artist", help="Filter by artist")
    playlist_parser.add_argument("--year", help="Filter by year")
    playlist_parser.add_argument("--format", choices=["m3u", "json"], default="m3u",
                                help="Playlist format")
    
    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up database (remove missing files)")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate comprehensive report")
    report_parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize database manager
    db_manager = DatabaseManager(args.db)
    
    if args.command == "search":
        results = db_manager.search_tracks(args.query, args.field)
        print(f"Found {len(results)} tracks:")
        for track in results[:20]:  # Limit to 20 results
            artists = ", ".join(track.get("artists", []))
            genres = ", ".join(track.get("genres", []))
            print(f"  {track['track_id']}: {artists} - {track.get('title', 'Unknown')} [{genres}]")
    
    elif args.command == "stats":
        stats = db_manager.get_detailed_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.command == "export":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.format == "json":
            output_path = f"ncs_export_{timestamp}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(db_manager.data, f, indent=2, ensure_ascii=False)
        else:  # csv
            output_path = f"ncs_export_{timestamp}.csv"
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Track ID', 'Title', 'Artists', 'Genres', 'URL', 'Publish Date', 'File Size (MB)'])
                for track_id, track_data in db_manager.data["tracks"].items():
                    file_size_mb = round(track_data.get('file_size', 0) / (1024 * 1024), 2)
                    writer.writerow([
                        track_id,
                        track_data.get('title', ''),
                        '; '.join(track_data.get('artists', [])),
                        '; '.join(track_data.get('genres', [])),
                        track_data.get('url', ''),
                        track_data.get('publish_date', ''),
                        file_size_mb
                    ])
        print(f"Database exported to: {output_path}")
    
    elif args.command == "playlist":
        tracks = []
        
        if args.genre:
            tracks = db_manager.get_tracks_by_genre(args.genre)
        elif args.artist:
            tracks = db_manager.get_tracks_by_artist(args.artist)
        elif args.year:
            tracks = db_manager.get_tracks_by_year(args.year)
        else:
            tracks = [dict(track_data, track_id=track_id) 
                     for track_id, track_data in db_manager.data["tracks"].items()]
        
        if tracks:
            playlist_path = db_manager.export_playlist(tracks, args.format)
            print(f"Created playlist with {len(tracks)} tracks")
        else:
            print("No tracks found matching criteria")
    
    elif args.command == "cleanup":
        stats = db_manager.cleanup_database()
        print(f"Cleanup completed:")
        print(f"  Total tracks: {stats['total']}")
        print(f"  Missing files: {stats['missing_files']}")
        print(f"  Removed: {stats['removed']}")
    
    elif args.command == "report":
        report = db_manager.generate_report(args.output)
        if not args.output:
            print(report)

if __name__ == "__main__":
    main()