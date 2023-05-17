let mode = 'training';
const target = '192.168.4.1';
const xCourtPos = 36;
const yCourtPos = 16;
const xCourtOffset = 28;
const yCourtOffset = 32;
const xFigOffset1 = 1.98;
const xFigOffset2 = 3.97;
const yFigOffset = 2.26;
const bt = document.getElementById('train');
const bc = document.getElementById('config');
const dc = document.getElementById('dconf');
const fc = document.getElementById('fconf');
const divTraining = document.getElementById('dtrain');
const shotSelected = document.getElementById('shots-selected');
const shotSelection = document.getElementById('shots-selection');
const trainingModeValue = document.getElementById('training-mode');
const trainingOrderValue = document.getElementById('training-order');
const shotsValue = document.getElementById('shots');
const cycleValue = document.getElementById('cycle');
const nameError = document.getElementById('name-error')
const cycleError = document.getElementById('cycle-error')
const shotsError = document.getElementById('shots-error')
const modeError = document.getElementById('mode-error')
const orderError = document.getElementById('order-error')
const names = document.getElementById('names');
const shot = document.getElementById('name');
const speed = document.getElementById('speed');
const angle = document.getElementById('angle');
const slope = document.getElementById('slope');
const height = document.getElementById('height');

const ShotNameError = document.getElementById('name-error');
const speederror = document.getElementById('speed-error');
const angleerror = document.getElementById('angle-error');
const slopeerror = document.getElementById('slope-error');
const heighterror = document.getElementById('height-error');

let shots = [];
let trainingShots = [];
let areaSelected = 0;

const cons = (e) => {
  const g = e.currentTarget.id.replace('g-', '');
  resetCourt();
  e.currentTarget.setAttribute("class", 'selected');
  areaSelected = parseInt(g);
  if (mode === 'training') {
    fetch(`http://${target}/area/${g}`)
      .then(response => response.json())
      .then(response => {
        console.log('fetch area');
        divTraining.style.display = 'block';
        shots = [...response.shots];
        console.log(shots);
        let n = '';
        for (let i = 0; i < shots.length; ++i) {
          n += `<input type="button" onClick='select_shot(${i}, ${g})' value="${shots[i].name}"/>`;
        }
        shotSelection.innerHTML = n;
      })
  } else if (mode === 'config') {
    console.log('sent: ' + `http://${target}/area/${g}`)
    fetch(`http://${target}/area/${g}`)
      .then(r => r.json())
      .then(r => {
        console.log(r);
        fc.style.display = 'block';
        shots = [...r.shots];
        let n = `<option id='new' selected>New</option>`;
        for (let i = 0; i < shots.length; ++i) {
          n += `<option id='o-${i}'>${shots[i].name}</option>`;
        }
        names.innerHTML = n;
      });
  }
}

//// Court

function resetCourt() {
  const allAreaButtons = document.getElementsByTagName('g');
  for (let i = 0; i < allAreaButtons.length; ++i) {
    allAreaButtons[i].setAttribute("class", '');
  }
}

//// Training area

function clear_training() {
  trainingShots = [];
  shotSelected.innerHTML = '';
  resetCourt();
}

function select_shot(index, area) {
  console.log(trainingShots);
  trainingShots.push({ ...shots[index].config, recovery: 0, delay: 0 });
  console.log(trainingShots);
  shotSelected.innerHTML += `<li>${area}. ${shots[index].name}</li>`;
}


function checkTextValue(e, id, expectedType) {

let err = true;
for (let i = 2; i < arguments.length; ++i) {
if (typeof e.value === expectedType && arguments[i] === e.value) {
  err = false;
  break;
}
}

if (err) {
document.getElementById(id).innerText = 'Please choose a correct value';
document.getElementById(id).className = 'input-error show';
return 1;
} else {
document.getElementById(id).innerText = '';
document.getElementById(id).className = 'input-error';
return 0;
}
}


//checkValue(this,"shot-error",0,600)
function checkValue(e, id, min, max) {
  const errorCheck = Number(e.value);
  if (isNaN(errorCheck)) {
    document.getElementById(id).innerText = 'Please provide a valid number';
    document.getElementById(id).className = 'input-error show';
    return 1;
  } else if (errorCheck < min || errorCheck > max) {
    document.getElementById(id).innerText = `Please provide a number between ${min} and ${max}`;
    document.getElementById(id).className = 'input-error show';
    return 1;
  } else {
    document.getElementById(id).innerText = '';
    document.getElementById(id).className = 'input-error';
    return 0;
  }
}

function checkTraining() {
  let retValue = 0;

  retValue += checkTextValue(trainingModeValue, 'training-mode-error', 'loop', 'once');
  retValue += checkTextValue(trainingOrderValue, 'training-order-error', 'random', 'normal');
  retValue += checkValue(shotsValue, 'shots-error', 0, 600);
  retValue += checkValue(cycleValue, 'cycle-error', 0, 60);

  return retValue;
}

function launch_training() {
  let errorValue = checkTraining();
  console.log(errorValue);
  if (!errorValue && trainingShots.length > 0) {
    const trainingProgram = {
      seq: [...trainingShots],
      mode: trainingModeValue.value,
      order: trainingOrderValue.value,
      cycle: Number(cycleValue.value),
      shots: Number(shotsValue.value)
    }
    const body = JSON.stringify(trainingProgram);
    console.log(body);
    fetch(`http://${target}/training`, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: body
    })
      .then(r => r.json())
      .then(r => {
        console.log(r);
        resetCourt();
      });
  }
}

//////////////////////


//// Config area

function checkEmptyValue(e, id) {
  if (e.value.trim() === '') {
    document.getElementById(id).innerText = `Please provide a name`;
    document.getElementById(id).className = 'input-error show';
    return 1;
  } else {
    document.getElementById(id).innerText = '';
    document.getElementById(id).className = 'input-error';
    return 0;

  }
}

function checkConfig() {
  let retValue = 0;

  retValue = checkEmptyValue(shot, 'name-error');
  retValue += checkValue(speed, 'speed-error', 0, 100);
  retValue += checkValue(angle, 'angle-error', 0, 180);
  retValue += checkValue(slope, 'slope-error', 0, 180);
  retValue += checkValue(height, 'height-error', 0, 40);

  return retValue;
}

function preview() {
  console.log('preview');
  let err = checkConfig();
  if (err === 0) {
    console.log(`http://${target}/preview`);
    const test = {
      speed: speed.value,
      angle: angle.value,
      slope: slope.value,
      height: height.value
    };
    const body = JSON.stringify(test);
    fetch(`http://${target}/preview`, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: body
    })
      .then(r => r.json())
      .then(r => {
        console.log(r);
      });
  } else {
    console.log(err)
  }
}

function stop() {
  console.log('preview');
  fetch(`http://${target}/stop`)
    .then(r => r.json())
    .then(r => {
      console.log(r);
    });
}

function quit() {
  fetch(`http://${target}/quit`)
    .then(r => r.json())
    .then(r => {
      console.log(r);
    });
}

function updateShot() {
  console.log('test');
  const n = names.options[names.selectedIndex].id;
  if (n !== 'new') {
    const i = parseInt(n.replace('o-', ''));
    shot.value = shots[i].name;
    speed.value = shots[i].config.speed;
    angle.value = shots[i].config.angle;
    slope.value = shots[i].config.slope;
    height.value = shots[i].config.height;
  }
  console.log(n)
}
function save() {
  let err = checkConfig();
  if (err === 0) {
    const newShot = {
      name: shot.value.trim(),
      config: {
        speed: speed.value,
        angle: angle.value,
        slope: slope.value,
        height: height.value
      }
    };
    const body = JSON.stringify(newShot);
    console.log('Element sent: ' + body);
    fetch(`http://${target}/area/${areaSelected}/${newShot.name}`, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: body
    })
      .then(r => r.json())
      .then(r => {
        console.log(r);
        resetCourt();
      });
    fc.style.display = 'none';
    names.innerHTML = '';
    shot.value = '';
    speed.value = '';
    angle.value = '';
    slope.value = '';
    height.value = '';
  }
}


function cancel() {
  fc.style.display = 'none';
  names.innerHTML = '';
  shot.value = '';
  speed.value = '';
  angle.value = '';
  slope.value = '';
  height.value = '';
  resetCourt();
}
function toggleMode(m) {
  mode = m;
  if (m === 'training') {
    dc.style.display = 'none';
    fc.style.display = 'none';
    divTraining.style.display = 'block'
    bt.className = '';
    bc.className = 'b';
    bt.disabled = true;
    bc.disabled = false;
  } else {
    dc.style.display = 'block';
    divTraining.style.display = 'none'
    bt.className = 'b';
    bc.className = '';
    bt.disabled = false;
    bc.disabled = true;
  }
  resetCourt();
}

function courtLoad(fn) {
  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(fn, 1);
  } else {
    document.addEventListener("DOMContentLoaded", fn);
  }
}

courtLoad(function () {
  toggleMode('training');
  const svg = document.getElementById('court');
  for (let i = 0; i < 7; ++i) {
    for (let j = 0; j < 7; ++j) {
      const id = 7 * j + i + 1;
      const xFigOffset = id < 10 ? xFigOffset1 : xFigOffset2;
      const g = document.createElementNS('http://www.w3.org/2000/svg', "g");
      g.addEventListener('click', cons);
      g.id = `g-${id}`;
      g.innerHTML = `<circle cx="${xCourtPos + xCourtOffset * i}" cy="${yCourtPos + yCourtOffset * j}" r="7"/><text transform="translate(${xCourtPos + xCourtOffset * i - xFigOffset} ${yCourtPos + yCourtOffset * j + yFigOffset}) scale(1.12 1)">${id}</text>`;
      svg.appendChild(g);
    }
  }
});