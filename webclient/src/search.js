import 'bootstrap/dist/css/bootstrap.min.css';

const URLPARAMS = new URLSearchParams(window.location.search)
const ace = require('ace-builds');

const searchBoilerplate = 
`**kern
*clefG2
*k[]
=-
`;

var ACE_EDITOR;

function renderSvgFromXml(xml) {
	var vrvToolkit = new verovio.toolkit();

	var options = {
		inputFormat: "xml",
		scale: 40,
		font: "Leipzig",
		adjustPageHeight: 1,
		noFooter: 1,
		noHeader: 1
	}
	vrvToolkit.setOptions(options)
	var svg = vrvToolkit.renderData(xml, options);
	return svg
}

function renderQuery(krn) {
	var vrvToolkit = new verovio.toolkit();

	var options = {
		scale: 60,
		font: "Leipzig",
		adjustPageHeight: 1,
		noFooter: 1,
		noHeader: 1
	}
	vrvToolkit.setOptions(options)

	var svg = vrvToolkit.renderData(krn, options);
	return svg
}

function setQuery(krn) {
	/* -> updates hidden form field
	 * -> renders verovio
	 */
	var svgContainer = document.getElementById("humdrum-viewer");
	svgContainer.innerHTML = renderQuery(krn);
	document.forms["search"].elements["query"].value = krn;
}

function uncollapseKrn(krn) {
	var vertical = krn.replace(new RegExp(" ", "g"), "\n");
	var horizontal = vertical.replace(new RegExp(",", "g"), " ");
	return horizontal
}

function renderOccurrencePanel(i, occJson, xml) {
    var svg = renderSvgFromXml(xml)
    console.log("rendering occ panel " + i.toString())
    document.getElementById("occ-" + i.toString()).innerHTML = svg

    var headerText = "Piece ID #" + occJson["pid"] + " " + occJson["name"]
    document.getElementById("occ-" + i.toString() + "-header").innerHTML = headerText
}

function getAndRenderPageExcerpts(pageJsonArray) {
    for (var i=0; i < pageJsonArray.length; i++) {
        (function(j) {
            var res = $.get(pageJsonArray[j]['excerptUrl']).done(function(res) {
                var sr = new XMLSerializer()
                var xml = sr.serializeToString(res.documentElement)
                renderOccurrencePanel(j, pageJsonArray[j], xml)
            });
        })(i);
    }
}

function ProcessResponse(searchResponse) {
	ACE_EDITOR.setValue(searchResponse['query'])
	
	// Svg Container
	setQuery(searchResponse['query']);

    getAndRenderPageExcerpts(searchResponse['pages'][URLPARAMS.get('page')])
    
    //:todo set all filters to the previous search request

    /*
	// Render Excerpts
	for (var i = 0; i < searchResponse['pages'][URLPARAMS.get('page')].length; i++) {
		var occJson = searchResponse['pages'][URLPARAMS.get('page')][i]
		if (occJson['excerptFailed']) {
			console.log("excerpt failed: " + occJson)
		} else {
            var xml = window.atob(occJson['xmlBase64'])
            renderOccurrencePanel(i, xml)
		}
	} 
    */
}

function newAceEditor() {
	ACE_EDITOR = ace.edit("ace-editor", {
			autoScrollEditorIntoView: true,
			value: searchBoilerplate,
			minLines: 10,
			maxLines: 10
	});

	// rerender the svg-container on change
	ACE_EDITOR.session.on('change', function(delta){
		setQuery(ACE_EDITOR.getValue())
	});
}

function setSearchForm(rpp, page) {
	var form = document.forms["search"]
	form.elements["rpp"].value = rpp;
	form.elements["page"].value = page;
}

function setInexactFilter(values) {
    var leftIndicator = document.getElementById("inexactSliderLeftIndicator");
    leftIndicator.innerHTML = values[0];
    var rightIndicator = document.getElementById("inexactSliderRightIndicator");
    rightIndicator.innerHTML = values[1];

    var form = document.forms["search"]
    form.elements["inexact"].value = values.join(',')
}

function setTranspositionFilter(values) {
    var leftIndicator = document.getElementById("transpositionSliderLeftIndicator");
    leftIndicator.innerHTML = values[0];
    var rightIndicator = document.getElementById("transpositionSliderRightIndicator");
    rightIndicator.innerHTML = values[1];

    var form = document.forms["search"]
    form.elements["tnps"].value = values.join(',')
}

function setWindowFilter(values) {
    var leftIndicator = document.getElementById("targetWindowSliderLeftIndicator");
    leftIndicator.innerHTML = values[0];
    var rightIndicator = document.getElementById("targetWindowSliderRightIndicator");
    rightIndicator.innerHTML = values[1];

    var form = document.forms["search"]
    form.elements["intervening"].value = values.join(',')
}

function setCollection(value) {
    var form = document.forms["search"]
    form.elements["collection"].value = value
}

function initFilters() {
    if (URLPARAMS.get("intervening")) {
        var windowSliderValues = URLPARAMS.get("intervening").split(",")
    } else {
        var windowSliderValues = [0, 0]
    }
    $("#targetWindowSlider").slider({
        range: true,
        min: 0,
        max: 15,
        values: windowSliderValues,
        slide: function(event, ui) {
            setWindowFilter(ui.values)
        }
    });
    setWindowFilter(windowSliderValues);

    if (URLPARAMS.get("tnps")) {
        var transpositionSliderValues = URLPARAMS.get("tnps").split(",")
    } else {
        var transpositionSliderValues = [0, 0]
    }
    $("#transpositionSlider").slider({
        range: true,
        min: -12,
        max: 12,
        values: transpositionSliderValues,
        slide: function(event, ui) {
            setTranspositionFilter(ui.values)
        }
    });
    setTranspositionFilter(transpositionSliderValues);

    if (URLPARAMS.get("inexact")) {
        var inexactSliderValues = URLPARAMS.get("inexact").split(",")
    } else {
        var inexactSliderValues = [0, 0]
    }
    $("#inexactSlider").slider({
        range: true,
        min: 0,
        max: 12,
        values: inexactSliderValues,
        slide: function(event, ui) {
            setInexactFilter(ui.values)
        }
    });
    setInexactFilter(inexactSliderValues);

    /*
    var palestrinaRadio = document.getElementById("collectionPalestrina");
    palestrinaRadio.addEventListener("click", function(event) {
        setCollection(3)    
    })
    var bachRadio = document.getElementById("collectionBach");
    bachRadio.addEventListener("click", function(event) {
        setCollection(2)    
    })
    setCollection(3)
    */
}


(() => {
	newAceEditor();
    initFilters();
	setSearchForm(5, 0);

	var searchResponse = JSON.parse(document.getElementById("searchResponse").innerHTML)
	if (Object.values(searchResponse).length !== 0)  {
		ProcessResponse(searchResponse)
	}
})();
