
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

const tooltip = d3.select("body")
    .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

async function main() {
    const songs = await d3.json("beatles_songs.json");

    // Declare the chart dimensions and margins.
    const width = 640;
    const height = 400;
    const marginTop = 80;
    const marginRight = 20;
    const marginBottom = 30;
    const marginLeft = 40;

    function graph(id, title, songs, verticalMax, fn) {
        // Declare the x (horizontal position) scale.
        const x = d3.scaleUtc()
            .domain([new Date("1957-01-01"), new Date("1970-12-31")])
            .range([marginLeft, width - marginRight]);

        // Declare the y (vertical position) scale.
        const y = d3.scaleLinear()
            .domain([0, verticalMax])
            .range([height - marginBottom, marginTop]);

        // Find or create the SVG container.
        let g = d3.select("#" + id);
        if (g.empty()) {
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

            // Add the graphed data.
            g = svg.append("g")
              .attr("stroke", "steelblue")
              .attr("stroke-width", 1.5)
              .attr("fill", "transparent")
              .attr("id", id);
        }

        g.selectAll("circle")
            .data(songs.filter(song => song.yendor !== undefined), song => song.title)
            .join(
                enter => enter.append("circle")
                            .attr("cx", song => x(new Date((song.yendor.year).toString())))
                            .attr("cy", song => y(fn(song)))
                            .on("mouseover", function(e, song) {
                                d3.select(this).transition()
                                    .duration(100)
                                    .attr("r", 7);
                                tooltip.transition()
                                    .duration(100)
                                    .style("opacity", 1);
                                tooltip.html(song.title)
                                    .style("left", (e.pageX + 10) + "px")
                                    .style("top", (e.pageY - 15) + "px");
                            })
                            .on("mouseout", function() {
                                d3.select(this).transition()
                                    .duration(100)
                                    .attr("r", 3);
                                tooltip.transition()
                                    .duration(100)
                                    .style("opacity", 0);
                            })
                            .transition()
                            .attr("r", 3),
                update => update,
                exit => exit
                            .transition()
                            .attr("r", 0)
                            .remove());
    }

    function refresh(doFiltering) {
        let filteredSongs = songs;
        if (doFiltering) {
            filteredSongs = filteredSongs.filter(song => song.yendor?.songwriter === "Lennon");
        }

        graph("duration",
              "Duration (Minutes)",
              filteredSongs.filter(song => song.yendor !== undefined),
              600,
              song => song.yendor.duration);
        graph("top50",
              "Top 50 Billboard",
              filteredSongs.filter(song => song.yendor !== undefined && song.yendor["top.50.billboard"] !== -1),
              60,
              song => song.yendor["top.50.billboard"]);
        graph("acousticness",
              "Acousticness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              1,
              song => song.chadwambles.acousticness);
        graph("danceability",
              "Danceability",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              1,
              song => song.chadwambles.danceability);
        graph("energy",
              "Energy",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              1,
              song => song.chadwambles.energy);
        graph("liveness",
              "Liveness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              1,
              song => song.chadwambles.liveness);
        graph("speechiness",
              "Speechiness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              1,
              song => song.chadwambles.speechiness);
        graph("valence",
              "Valence",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              1,
              song => song.chadwambles.valence);
    }

    refresh(false);

    const lennonOnlyCheckbox = d3.select("#lennonOnly");
    lennonOnlyCheckbox.on("change", () => refresh(lennonOnlyCheckbox.property("checked")));
}

main();
