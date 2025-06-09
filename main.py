import compute
import visualize
import sys

def main(audio_path: str, display_mode: str) -> None:
    y, sr = compute.read_audio(audio_path)
    frequency_bounds = compute.generate_frequency_bounds()
    bin_indices = compute.get_bin_indices(sr, frequency_bounds)
    db_arr = compute.make_db_arr(y, sr, bin_indices)
    visualize.display_window(audio_path, db_arr, display_mode)

main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "bar")


