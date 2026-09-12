import pyloudnorm as pyln

from mutagen.flac import FLAC
from mutagen import File

import librosa
import sys
from pathlib import Path

file_path = "01 Hung Up (Ranny ReWerk).mp3" # Beispiel-Dateipfad, bitte anpassen

def check_replaygain(file_path: str) -> bool:
    """Zeigt ReplayGain-Tags einer Datei an"""
    audio = File(file_path)
    if not audio or not audio.tags:
        print(f"""❌ Es wurden keine Tags in "{file_path}" gefunden""")

        return False

    tags = {k.upper(): v for k, v in audio.tags.items()}
    rg_tags = {k: v for k, v in tags.items() if 'REPLAYGAIN' in k}

    if rg_tags:
        #for tag, value in sorted(rg_tags.items()):
            #print(f"  {tag}: {value[0] if isinstance(value, list) else value}")

        return True

    else:
        print(f"""❌ Keine ReplayGain-Tags in "{file_path}" gefunden""")

        return False

def calculate_and_save_replaygain(file_path: str) -> bool:
    if not file_path.lower().endswith('.flac'):
        print(f"""❌ "{file_path}" ist keine FLAC-Datei. Überspringe...""")
        
    else:
        try:
            print("\n⌛ Berechne ReplayGain...")
            audio, sr = librosa.load(file_path, sr=None)
            meter = pyln.Meter(sr)
            loudness = meter.integrated_loudness(audio)
            loudness_normalized = pyln.normalize.loudness(audio, loudness, -18.0)
            peak = abs(loudness_normalized).max()

            flac = FLAC(file_path)
            flac["REPLAYGAIN_TRACK_GAIN"] = f"{-18.0 - loudness:.2f} dB"
            flac["REPLAYGAIN_TRACK_PEAK"] = f"{peak:.6f}"
            flac.save()

            print(f"✅ ReplayGain geschrieben: {-18.0 - loudness:.2f} dB")

            print("\n⌛ Verifiziere Daten...")

            if check_replaygain(file_path):
                print(f"""✅ Verifizierung erfolgreich für "{file_path}"!""")
                return True
            else:
                print(f"""⚠ Verifizierung fehlgeschlagen für "{file_path}"!""")
                return False

        except Exception as e:
            print(f"⚠ Fehler: {e}")
            return False

def process_folder(folder_path: str) -> dict:
    """Verarbeitet alle FLAC-Dateien in einem Ordner rekursiv"""
    folder = Path(folder_path)

    if not folder.is_dir():
        print(f"❌ Ordner nicht gefunden: {folder_path}")
        return {"success": 0, "failed": 0, "skipped": 0}

    flac_files = list(folder.rglob("*.flac"))

    if not flac_files:
        print(f"❌ Keine FLAC-Dateien in {folder_path} gefunden")
        return {"success": 0, "failed": 0, "skipped": 0}

    print(f"\n⌛ Verarbeite {len(flac_files)} FLAC-Datei(en) in {folder_path}\n")

    stats = {"success": 0, "failed": 0, "skipped": 0}
    failed = []

    for file_path in sorted(flac_files):
        print(f"\n{'='*60}")
        print(f"🎶 Datei: {file_path.name}")

        try:
            if check_replaygain(str(file_path)):
                print("ℹ  ReplayGain vorhanden, übersprungen")
                stats["skipped"] += 1
            else:
                if calculate_and_save_replaygain(str(file_path)):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    failed.append((str(file_path), None))

        except Exception as e:
            print(f"⚠ Fehler bei der Verarbeitung von {file_path.name}: {e}")
            stats["failed"] += 1
            failed.append((str(file_path), str(e)))

    # Zusammenfassung
    print(f"\n{'='*60}")
    print(f"  ✅ Erfolgreich: {stats['success']}")
    print(f"  ❌ Fehlgeschlagen: {stats['failed']}")
    print(f"  🐇 Übersprungen: {stats['skipped']}")
    print(f"")

    for file, error in failed:
        if error:
            print(f"""  ⚠ Fehler bei: "{file}": {error}""")

        else:
            print(f"""  ⚠ Fehler bei: "{file}" """)

    print(f"")
    print(f"{'='*60}\n")

    return stats


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if Path(path).is_dir():
            process_folder(path)
        else:
            calculate_and_save_replaygain(path)
    else:
        print("⚠  Bitte geben Sie einen Dateipfad oder Ordnerpfad als Argument an.")