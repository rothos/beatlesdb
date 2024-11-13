
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

const tooltip = d3.select("body")
    .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

async function main() {
    const songs = (await d3.json("beatles_songs.json"))
        .filter(song => song.yendor !== undefined && song.yendor.year <= 1970);

    // Declare the chart dimensions and margins.
    const width = 640;
    const height = 400;
    const marginTop = 80;
    const marginRight = 20;
    const marginBottom = 30;
    const marginLeft = 40;

    function graph(id, title, songs, fn) {
        // Declare the x (horizontal position) scale.
        const x = d3.scaleLinear()
            .domain([1957, 1970])
            .range([marginLeft, width - marginRight]);

        // Declare the y (vertical position) scale.
        const y = d3.scaleLinear()
            .domain([0, d3.max(songs, fn)])
            .range([height - marginBottom, marginTop]);

        // Find or create the SVG container.
        let svg = d3.select("#" + id);
        if (svg.empty()) {
            svg = d3.select("body")
                .append("svg")
                    .attr("id", id)
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
                .attr("class", "x-axis")
                .call(d3.axisBottom(x));

            // Add the y-axis.
            svg.append("g")
                .attr("transform", `translate(${marginLeft},0)`)
                .attr("class", "y-axis")
                .call(d3.axisLeft(y));

            // Area for standard deviation
            svg.append("path")
                .attr("class", "stddev-area")
                .attr("fill", "steelblue")
                .attr("stroke", "none")
                .style("opacity", 0.1);

            // Line for mean.
            svg.append("path")
                .attr("class", "mean-line")
                .attr("fill", "none")
                .attr("stroke", "steelblue")
                .attr("stroke-width", 1.5)
                .style("opacity", 0.3);

            // Add the graphed data.
            svg.append("g")
                .attr("class", "data-points")
                .attr("stroke", "steelblue")
                .attr("stroke-width", 1.5)
                .attr("fill", "transparent");
        }

        svg.select(".data-points")
            .selectAll("circle")
            .data(songs, song => song.title)
            .join(
                enter => enter.append("circle")
                            .attr("cx", song => x(song.yendor.year))
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

        // Map from year to { mean, stdev } object.
        const stats = d3.rollups(songs,
                                 d => ({ mean: d3.mean(d, fn), stddev: d3.deviation(d, fn) }),
                                 d => d.yendor.year)
                                 .map(d => ({ year: d[0], mean: d[1].mean, stddev: d[1].stddev ?? 0 }))
                                 .sort((a, b) => a.year - b.year);
                                 console.log(stats);

        svg.select(".stddev-area")
            .data([stats])
            .transition()
            .attr("d", d3.area()
                .x(d => x(d.year))
                .y0(d => y(d.mean - d.stddev))
                .y1(d => y(d.mean + d.stddev)));

        svg.select(".mean-line")
            .data([stats])
            .transition()
            .attr("d", d3.line()
                .x(d => x(d.year))
                .y(d => y(d.mean)));
    }

    function refresh(doFiltering) {
        let filteredSongs = songs;
        if (doFiltering) {
            filteredSongs = filteredSongs.filter(song => song.yendor.songwriter === "Lennon");
        }

        graph("duration",
              "Duration (Minutes)",
              filteredSongs,
              song => song.yendor.duration);
        graph("top50",
              "Top 50 Billboard",
              filteredSongs.filter(song => song.yendor["top.50.billboard"] !== -1),
              song => song.yendor["top.50.billboard"]);
        graph("acousticness",
              "Acousticness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.acousticness);
        graph("danceability",
              "Danceability",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.danceability);
        graph("energy",
              "Energy",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.energy);
        graph("liveness",
              "Liveness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.liveness);
        graph("speechiness",
              "Speechiness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.speechiness);
        graph("valence",
              "Valence",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.valence);
    }

    refresh(false);

    const lennonOnlyCheckbox = d3.select("#lennonOnly");
    lennonOnlyCheckbox.on("change", () => refresh(lennonOnlyCheckbox.property("checked")));
}

main();
