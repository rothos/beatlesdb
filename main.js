
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

async function main() {
    const result = await fetch("beatles_songs.json");
    const songs = await result.json();

    // Declare the chart dimensions and margins.
    const width = 640;
    const height = 400;
    const marginTop = 80;
    const marginRight = 20;
    const marginBottom = 30;
    const marginLeft = 40;

    function addGraph(title, songs, verticalMax, fn) {
        // Declare the x (horizontal position) scale.
        const x = d3.scaleUtc()
            .domain([new Date("1957-01-01"), new Date("1970-12-31")])
            .range([marginLeft, width - marginRight]);

        // Declare the y (vertical position) scale.
        const y = d3.scaleLinear()
            .domain([0, verticalMax])
            .range([height - marginBottom, marginTop]);

        // Create the SVG container.
        const svg = d3.select("body")
            .append("svg")
                .attr("width", width)
                .attr("height", height);

        svg.append("text")
            .attr("x", width / 2)
            .attr("y", marginTop - 20)
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .text(title);

        // Add the x-axis.
        svg.append("g")
            .attr("transform", `translate(0,${height - marginBottom})`)
            .call(d3.axisBottom(x));

        // Add the y-axis.
        svg.append("g")
            .attr("transform", `translate(${marginLeft},0)`)
            .call(d3.axisLeft(y));

        svg.append("g")
          .attr("stroke", "steelblue")
          .attr("stroke-width", 1.5)
          .attr("fill", "none")
        .selectAll("circle")
        .data(songs.filter(song => song.yendor !== undefined))
        .join("circle")
          .attr("cx", song => x(new Date((song.yendor.year).toString())))
          .attr("cy", song => y(fn(song)))
          .attr("r", 3);
    }

    addGraph("Duration (Minutes)", songs.filter(song => song.yendor !== undefined), 600, song => song.yendor.duration);
    addGraph("Top 50 Billboard", songs.filter(song => song.yendor !== undefined && song.yendor["top.50.billboard"] !== -1),
             60, song => song.yendor["top.50.billboard"]);
    addGraph("Acousticness", songs.filter(song => song.chadwambles !== undefined), 1, song => song.chadwambles.acousticness);
    addGraph("Danceability", songs.filter(song => song.chadwambles !== undefined), 1, song => song.chadwambles.danceability);
    addGraph("Energy", songs.filter(song => song.chadwambles !== undefined), 1, song => song.chadwambles.energy);
    addGraph("Liveness", songs.filter(song => song.chadwambles !== undefined), 1, song => song.chadwambles.liveness);
    addGraph("Speechiness", songs.filter(song => song.chadwambles !== undefined), 1, song => song.chadwambles.speechiness);
    addGraph("Valence", songs.filter(song => song.chadwambles !== undefined), 1, song => song.chadwambles.valence);
}

main();
