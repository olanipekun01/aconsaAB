


let btn = document.querySelector('#btn');
let sidebar = document.querySelector('.sidebar');
let searchBtn = document.querySelector('.bx-search');

        





    function handleEachResultModal(code) {
        document.querySelector(".upload_result").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
        document.querySelector('.uploadTitle').value = code;
    }

    function closeEachResultModal() {
        event.preventDefault();
        document.querySelector(".upload_result").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }

    function handleGradeUpdateModal(id, title, code) {
        document.querySelector(".update_grade").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
        document.querySelector('#gradeCode').innerHTML = code;
        document.querySelector('#gradeTitle').innerHTML = title;
        document.querySelector('#registrationIdInput').value = id;
    }

    function closeGradeModal() {
        event.preventDefault();
        document.querySelector(".update_grade").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }

    function handleCreateModal() {
        document.querySelector(".create_programme").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
    }

    


    function closeCreateModal() {
        event.preventDefault();
        document.querySelector(".create_programme").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }

    function handleUpdateModal(name, duration, degree, id) {
        document.querySelector(".update_programme").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
        document.querySelector('#updateModalDegreeInput').value = degree;
        document.querySelector('#updateModalDurationInput').value = duration;
        document.querySelector('#updateModalNameInput').value = name;  
        document.querySelector('#updateModalIdInput').value = id;
    }

    function closeUpdateModal() {
        event.preventDefault();
        document.querySelector(".update_programme").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }


    function handleDeptCreateModal() {
        document.querySelector(".create_department").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
    }

    function closeDeptCreateModal() {
        event.preventDefault();
        document.querySelector(".create_department").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }

    function handleDeptUpdateModal(name, id) {
        document.querySelector(".update_department").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
        document.querySelector('#updateModalNameInput').value = name;  
        document.querySelector('#updateModalIdInput').value = id;
    }

    function closeDeptUpdateModal() {
        event.preventDefault();
        document.querySelector(".update_department").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }

    function showFilterModal() {
        // document.querySelector(".issue_modal_container").style.display = "block";
        document.querySelector(".filter_container").style.display = "block";
    };

    function closeFilterModal() {
        event.preventDefault();
        document.querySelector(".filter_container").style.display = "none";
        // document.querySelector(".background_wrapper").style.display = "none";
    }

    // document.getElementById("cancelBtn").addEventListener("click", function (event) {
    //     event.preventDefault();
    //     document.querySelector(".modal_container").style.display = "none";
    // })


    function handleDeletePopOut(link, name) {
        document.querySelector(".deletePopOut").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
        document.querySelector(".popOutItemLink").href = link;
        document.querySelector(".popOutItemName").innerHTML = name;
    }


    function closePopOut() {
        event.preventDefault();
        document.querySelector(".deletePopOut").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }



    btn.onclick = function () {
        sidebar.classList.toggle("active");
    }

    searchBtn.onclick = function () {
        sidebar.classList.toggle("active");
    }

    function handleCourseUpdateModal(title, code, unit, status, semester, courseCat, level, id, selectedProgrammes) {
    // function handleCourseUpdateModal(title, code, unit, status, semester, level, id) {
        
        console.log('details', title, code, semester, unit, status, level, courseCat);
        document.querySelector(".update_programme").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
        document.querySelector(".update_programme").style.display = "block";
        document.querySelector(".background_wrapper").style.display = "block";
        document.querySelector('#updateCourseTitleInput').value = title;
        document.querySelector('#updateCourseCodeInput').value = code;
        document.querySelector('#updateCourseUnitInput').value = unit;  
        document.querySelector('#updateCourseStatusInput').value = status; 
        document.querySelector('#updateCourseCat').value = courseCat;  
        document.querySelector('#updateCourseSemesterInput').value = semester;
        document.querySelector('#updateCourseLevelInput').value = level; 
        document.querySelector('#updateCourseIdInput').value = id;

        document.querySelectorAll('.course-checkbox').forEach(checkbox => {
            if (selectedProgrammes.includes(checkbox.value)) {
                checkbox.checked = true;
            } else {
                checkbox.checked = false;
            }
        });

        // document.querySelectorAll('.course-checkbox').forEach(checkbox => {
        //     checkbox.checked = false;
        // });
    
        // // Check the boxes for selected programs
        // selectedProgrammes.forEach(programmeId => {
        //     const checkbox = document.querySelector(`.course-checkbox[value="${programmeId}"]`);
        //     console.log("Checkbox found for programmeId:", programmeId, checkbox);
        //     if (checkbox) {
        //         checkbox.checked = true;
        //     }
        // });
    }

    const courses = JSON.parse('{{ courses|safe }}');
    

    // function handleCourseUpdateModal(title, code, unit, status, semester, level, id) {
        
    //     document.querySelector(".update_programme").style.display = "block";
    //     document.querySelector(".background_wrapper").style.display = "block";
    //     const course = courses.find(c => c.id === id);
        
    //     if (course) {
    //         document.querySelector('#updateCourseTitleInput').value = title;
    //         document.querySelector('#updateCourseCodeInput').value = code;
    //         document.querySelector('#updateCourseUnitInput').value = unit;  
    //         document.querySelector('#updateCourseStatusInput').value = status;  
    //         document.querySelector('#updateCourseSemesterInput').value = semester;
    //         document.querySelector('#updateCourseLevelInput').value = level; 
    //         document.querySelector('#updateCourseIdInput').value = id;
    //         document.querySelectorAll('.course-checkbox').forEach(checkbox => {
    //             checkbox.checked = false;
    //         });

    //         course.programmes.forEach(programmeId => {
    //             const checkboxes = document.querySelectorAll(`.course-checkbox[value="${programmeId}"]`);
    //             checkboxes.forEach(checkbox => {
    //                 checkbox.checked = true;
    //             });
    //         });
    //     }
    // }

    function closeCourseUpdateModal() {
        event.preventDefault();
        document.querySelector(".update_programme").style.display = "none";
        document.querySelector(".background_wrapper").style.display = "none";
    }



    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Check if this cookie string starts with the name we want
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // function sendData(matric) {
    //     console.log('im here');
        // const formData = new FormData();
        // formData.append('matricNo', matric);

        // fetch('http://localhost:8000/instructor/student/management/', {
        //     method: 'POST',
        //     headers: {
        //         'X-CSRFToken': getCookie('csrftoken')
        //     },
        //     body: formData
        // })
        // .then(response => response.json())
        // .then(data => {
        //     console.log('Success:', data);
        // })
        // .catch((error) => {
        //     console.error('Error:', error);
        // });
    // }