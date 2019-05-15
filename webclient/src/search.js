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

function renderSvgFromBase64Xml(xmlBase64) {
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
	var xml = window.atob(xmlBase64)
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

function ProcessResponse(searchResponse) {
	ACE_EDITOR.setValue(searchResponse['query'])
	
	// Svg Container
	setQuery(searchResponse['query']);

	// Render Excerpts
	for (var i = 0; i < searchResponse['rpp']; i++) {
		var occJson = JSON.parse(searchResponse['pages'][URLPARAMS.get('page')][i])
		if (occJson['excerptFailed']) {
			console.log("excerpt failed: " + occJson)
		} else {
			var svg = renderSvgFromBase64Xml(occJson['xmlBase64'])
			document.getElementById("occ-" + i.toString()).innerHTML = svg
		}
	} 
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

(() => {
	newAceEditor();
	setSearchForm(5, 0);

	var searchResponse = JSON.parse(document.getElementById("searchResponse").innerHTML)
	//var searchResponse = {pageCount: URLPARAMS.get('pageCount'), page: URLPARAMS.get('page'), rpp: URLPARAMS.get('rpp'), query: URLPARAMS.get('query')}

	if (Object.values(searchResponse).length !== 0)  {
		ProcessResponse(searchResponse)
	}
})();
