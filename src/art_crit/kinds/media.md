{prompt}

Deliver the result as image and/or video files, working in the current directory.
- Save the finished files in ./output/. Only what is in ./output/ is published as the result, so
  ./output/ holds those finished image/video files and nothing else.
- Formats: images as .png, .jpg, .webp, .gif or .svg; videos as .mp4 or .webm. At most 8 files,
  each under 2 MB; videos at most 10 seconds.
- To check your work, look at what you made (a still, a rendered frame, a few frames of the video), and
  save what you look at as .jpg rather than .png: each image you read stays in your context, and a long
  session of large .png files can hit the provider's per-request image limit and end the run.
- Tools available on this machine: {tools}. Don't install packages or download anything.
- Keep the code you write to make the files in the working directory (its root, or a subdirectory
  like ./src/, but not in ./output/): it's published as the source. Delete intermediate files such
  as rendered frames when you're done.
- Only create or edit files inside the current directory.
- End your final message with a line starting with `Blurb:`, then one to three sentences in the third
  person describing what you made for a visitor who will see it on the site: name the work if it has a
  name, and say what it is and what it does or is about. No file names, commands, instructions or claims
  about tests. For example: "Blurb: Ripple is a game that teaches players to spot online misinformation."
