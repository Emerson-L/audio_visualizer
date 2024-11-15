import compute
import visualize

#audio_path = '/Users/emersonlange/Documents/songs/upsidedowndinner.mp3'
audio_path = "/Users/emersonlange/Documents/songs/shangalangin.mp3"
#audio_path = '/Users/emersonlange/Documents/songs/visualizer_testaudio.mp3'

#Choose from bar or line
display_mode = "line"

def main(audio_path: str) -> None:
    y, sr = compute.read_audio(audio_path)
    frequency_bounds = compute.generate_frequency_bounds()
    bin_indices = compute.get_bin_indices(sr, frequency_bounds)
    db_array = compute.make_db_array(y, sr, bin_indices)
    visualize.display_window(audio_path, db_array, display_mode)

#what does if name == main do??
main(audio_path)


