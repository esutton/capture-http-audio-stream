import requests


UrlMp3 = "https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3"

def stream_radio(url, output_file):
    print(f"Connecting to {url} ...")
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()  # Ensure we got a valid response
            print("Connected! Streaming... (Press CTRL+C to stop)")
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)
    except KeyboardInterrupt:
        print("\nStopped by user (CTRL+C).")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace with The Spy FM's actual stream URL
    stream_url = UrlMp3  # Example placeholder, replace as needed
    output_filename = "spyfm_capture.mp3"
    
    stream_radio(stream_url, output_filename)
    print(f"Saved to: {output_filename}")