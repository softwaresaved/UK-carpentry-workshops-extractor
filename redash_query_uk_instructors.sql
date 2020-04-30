-- A query to extract all UK instructors
SELECT workshops_person.personal as first_name,
 workshops_person.family as last_name,
 workshops_person.affiliation AS institution,
 workshops_person.country AS country_code,
 teachings.workshops AS taught_workshops,
 teachings.workshop_dates AS taught_workshop_dates,
 knowledge_domains.domains AS domains,
 group_concat(workshops_badge.name) AS badges,
 group_concat(workshops_award.awarded) AS badges_dates,
 workshops_airport.fullname AS airport,
 workshops_airport.iata AS airport_code,
 workshops_airport.latitude AS airport_latitude,
 workshops_airport.longitude AS airport_longitude
FROM workshops_person
JOIN workshops_award ON workshops_person.id = workshops_award.person_id
JOIN workshops_badge ON (workshops_badge.id = badge_id and workshops_badge.title like '%instructor%')
LEFT JOIN workshops_airport ON workshops_person.airport_id = workshops_airport.id
LEFT JOIN
  (SELECT workshops_person_domains.person_id AS person_id,
          group_concat(workshops_knowledgedomain.name) AS domains
   FROM workshops_person_domains
   JOIN workshops_knowledgedomain ON workshops_person_domains.knowledgedomain_id = workshops_knowledgedomain.id
   GROUP BY workshops_person_domains.person_id) AS knowledge_domains ON workshops_person.id = knowledge_domains.person_id
LEFT JOIN
  (SELECT workshops_task.person_id, --   group_concat(workshops_role.name) AS workshop_tasks,
 group_concat(workshops_event.slug) AS workshops,
 group_concat(workshops_event.start) AS workshop_dates
   FROM workshops_task
   LEFT JOIN workshops_role ON workshops_task.role_id = workshops_role.id
   JOIN workshops_event ON workshops_task.event_id = workshops_event.id
   WHERE workshops_role.name == "instructor"
   GROUP BY workshops_task.person_id) AS teachings ON teachings.person_id = workshops_person.id
WHERE workshops_person.country == "GB"
  OR workshops_airport.country == "GB"
GROUP BY workshops_person.id