function splitForPeople(formattingStr, numPeople, splitting) {
  let pageNum = 0;
  var result = '';
  const footnoteSplitRemainderStart = numPeople - (splitting % numPeople) - 1;

  for (let i = 0; i < numPeople; i++) {
    const startPage = pageNum + 1;

    if (i > footnoteSplitRemainderStart) {
      pageNum++;
    }

    pageNum += Math.floor(splitting / numPeople);
    const finishPage = pageNum;

    result += `${formattingStr}${startPage}-${finishPage}\n`;
    console.log(`${formattingStr}${startPage}-${finishPage}`);
  }
  return result;
}

function splitForPeoplePages(formattingStr, numPeople, splitting) {
  let pageNum = 0;
  // const footnoteSplitRemainderStart = numPeople - (splitting % numPeople) - 1;

  const perPersonPages = Math.floor(splitting / numPeople) * 2 + Math.floor((splitting % numPeople) / 2);
  const numPeopleHalf = Math.floor(numPeople / 2) + (numPeople % 2);
  var result = '';

  for (let i = 0; i < numPeopleHalf; i++) {
    const startPage = pageNum + 1;

    // if (i > footnoteSplitRemainderStart) {
    //   pageNum++;
    // }

    pageNum += (pageNum + perPersonPages) < splitting ? perPersonPages : splitting - pageNum;
    const finishPage = pageNum;

    if (i === numPeopleHalf - 1 && numPeople % 2 === 1) {
      result += `-   1 student on pgs ${startPage}-${finishPage}\n`;
      console.log(`-   1 student on pgs ${startPage}-${finishPage}`);
    } else {
      result += `${formattingStr}${startPage}-${finishPage}\n`;
      console.log(`${formattingStr}${startPage}-${finishPage}`);
    }
  }
  return result;
}

function splitFootnotes(numPeople, footnotes) {
  const formatting = '-   1 student on ';
  return splitForPeople(formatting, numPeople, footnotes);
}

function splitPages(numPeople, pages) {
  const formatting = '-   2 students on pgs ';
  return splitForPeoplePages(formatting, numPeople, pages);
}

function generateOutput() {
  // Get input values
  var numFootnotes = parseInt(document.getElementById('numFootnotes').value);
  var numPages = parseInt(document.getElementById('numPages').value);
  var numPeople = parseInt(document.getElementById('numPeople').value);

  console.log(splitFootnotes(numPeople, numFootnotes));

  var footnoteOutput = "Footnotes split:\n" + splitFootnotes(numPeople, numFootnotes) + "\n\n";
  var pageOutput = "Pages split:\n" + splitPages(numPeople, numPages);
  // Display the output
  document.getElementById('output').innerHTML = footnoteOutput + pageOutput;
}