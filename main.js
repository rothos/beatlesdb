
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

const tooltip = d3.select("body")
    .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

async function main() {
    const songs = (await d3.json("beatles_songs.json"))
        .filter(song => song.yendor !== undefined && song.yendor.year >= 1962 && song.yendor.year <= 1970);

    // Declare the chart dimensions and margins.
    const width = 640;
    const height = 400;
    const marginTop = 80;
    const marginRight = 20;
    const marginBottom = 30;
    const marginLeft = 40;

    function graph(id, title, format, songs, xFn, yFn) {
        if (id === "foo") {
            console.log(songs);
        }
        // Declare the x (horizontal position) scale.
        const x = d3.scaleLinear()
            .domain([d3.min(songs, xFn), d3.max(songs, xFn)])
            .range([marginLeft, width - marginRight]);

        // Declare the y (vertical position) scale.
        const y = d3.scaleLinear()
            .domain([0, d3.max(songs, yFn)])
            .range([height - marginBottom, marginTop]);

        const xAxis = d3.axisBottom(x).tickFormat(d3.format(format));
        const yAxis = d3.axisLeft(y);

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
                .attr("class", "x-axis");

            // Add the y-axis.
            svg.append("g")
                .attr("transform", `translate(${marginLeft},0)`)
                .attr("class", "y-axis");

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

        // Update axes.
        svg.selectAll(".x-axis")
            .transition()
            .call(xAxis);
        svg.selectAll(".y-axis")
            .transition()
            .call(yAxis);

        // Update data points.
        svg.select(".data-points")
            .selectAll("circle")
            .data(songs, song => song.title)
            .join(
                enter => enter.append("circle")
                            .attr("cx", song => x(xFn(song)))
                            .attr("cy", song => y(yFn(song)))
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
                                 d => ({ mean: d3.mean(d, yFn), stddev: d3.deviation(d, yFn) }),
                                 song => xFn(song))
                                 .map(d => ({ year: d[0], mean: d[1].mean, stddev: d[1].stddev ?? 0 }))
                                 .sort((a, b) => a.year - b.year);

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

    function graphByYear(id, title, songs, yFn) {
        graph(id, title, "4d", songs, song => song.yendor.year, yFn);
    }

    function refresh(doFiltering) {
        let filteredSongs = songs;
        if (doFiltering) {
            filteredSongs = filteredSongs.filter(song => song.yendor.songwriter === "Lennon");
        }

        graphByYear("duration",
              "Duration (Seconds)",
              filteredSongs,
              song => song.yendor.duration);
        graphByYear("number_of_chords",
              "Number of Chords (Originals)",
              filteredSongs.filter(song => song.isophonics?.chordlab !== undefined && song.pannell?.album?.Original_songs === 1),
              song => new Set(song.isophonics.chordlab.map(cl => cl.chord).filter(chord => chord !== "N")).size);
        graphByYear("number_of_takes",
              "Number of Takes",
              filteredSongs.filter(song => song.pannell?.album !== undefined),
              song => song.pannell.album.Takes);
        graph("paul_billboard",
              "Paul Authorship (vs John) vs. Billboard",
              ".1f",
              filteredSongs.filter(song => song.pannell !== undefined &&
                                   song.yendor["top.50.billboard"] !== -1 &&
                                   Math.abs(song.pannell.album.Composer_share_John + song.pannell.album.Composer_share_Paul - 1) < 0.01),
              song => song.pannell.album.Composer_share_Paul,
              song => song.yendor["top.50.billboard"]);
        graphByYear("top50",
              "Top 50 Billboard",
              filteredSongs.filter(song => song.yendor["top.50.billboard"] !== -1),
              song => song.yendor["top.50.billboard"]);
        graphByYear("acousticness",
              "Acousticness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.acousticness);
        graphByYear("danceability",
              "Danceability",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.danceability);
        graphByYear("energy",
              "Energy",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.energy);
        graphByYear("liveness",
              "Liveness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.liveness);
        graphByYear("speechiness",
              "Speechiness",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.speechiness);
        graphByYear("valence",
              "Valence",
              filteredSongs.filter(song => song.chadwambles !== undefined),
              song => song.chadwambles.valence);
    }

    refresh(false);

    const lennonOnlyCheckbox = d3.select("#lennonOnly");
    lennonOnlyCheckbox.on("change", () => refresh(lennonOnlyCheckbox.property("checked")));
}

main();
