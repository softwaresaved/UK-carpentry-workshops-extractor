
-- All workshops ran in the UK or organised by an UK institution
-- Note that online workshops will have 'W3' as country so need to look into host country too
SELECT workshops.slug,
       workshops.start,
       workshops.end,
       workshops.attendance,
       workshops.country_code,
       workshops.organiser,
       workshops.organiser_domain as organiser_web_domain,
       workshops.organiser_country_code,
       workshops.venue,
       workshops.address,
       workshops.longitude,
       workshops.latitude,
       workshops.tags,
       workshops.website_url,
       workshop_requests.workshop_request_domains as workshop_domains
    --   workshop_requests.event_request_id
FROM
  (SELECT workshops_event.id,
          workshops_event.slug,
          workshops_event.venue,
          workshops_event.address,
          workshops_event.country AS country_code,
          workshops_event.longitude,
          workshops_event.latitude,
          workshops_event.start,
          workshops_event.end,
          workshops_event.url as website_url,
          workshops_event.manual_attendance AS attendance,
          workshops_organization.fullname AS organiser,
          workshops_organization.domain AS organiser_domain,
          workshops_organization.country AS organiser_country_code,
          string_agg(workshops_tag.name, ',') AS tags
   FROM workshops_event
   JOIN workshops_organization  ON workshops_event.host_id = workshops_organization.id
   JOIN workshops_event_tags ON workshops_event.id = workshops_event_tags.event_id
   JOIN workshops_tag ON workshops_event_tags.tag_id = workshops_tag.id
   WHERE workshops_event.country = 'GB' OR workshops_organization.country = 'GB'
   GROUP BY workshops_event.id, workshops_organization.fullname, workshops_organization.domain, workshops_organization.country
   ORDER BY date(workshops_event.start) DESC) AS workshops
LEFT JOIN
  (SELECT workshops_workshoprequest.id AS event_request_id,
          workshops_workshoprequest.event_id AS event_id,
          string_agg(workshops_knowledgedomain.name || ':', ',') AS workshop_request_domains
   FROM workshops_workshoprequest
   JOIN workshops_workshoprequest_domains ON workshops_workshoprequest.id = workshops_workshoprequest_domains.workshoprequest_id
   JOIN workshops_knowledgedomain ON workshops_workshoprequest_domains.knowledgedomain_id = workshops_knowledgedomain.id
   GROUP BY workshops_workshoprequest.id) AS workshop_requests ON workshops.id = workshop_requests.event_id;



-- ########### Old query before the rename of some tables in AMY #####################

-- All workshops ran in the UK or organised by an UK institution
-- Note that online workshops will have 'W3' as country so need to look into host country too
SELECT workshops.slug,
       workshops.start,
       workshops.end,
       workshops.attendance,
       workshops.country_code,
       workshops.organiser,
       workshops.organiser_domain as organiser_web_domain,
       workshops.organiser_country_code,
       workshops.venue,
       workshops.address,
       workshops.longitude,
       workshops.latitude,
       workshops.tags,
       workshops.website_url,
       workshop_requests.workshop_request_domains as workshop_domains
    --   workshop_requests.event_request_id
FROM
  (SELECT workshops_event.id,
          workshops_event.slug,
          workshops_event.venue,
          workshops_event.address,
          workshops_event.country AS country_code,
          workshops_event.longitude,
          workshops_event.latitude,
          workshops_event.start,
          workshops_event.end,
          workshops_event.url as website_url,
          workshops_event.manual_attendance AS attendance,
          workshops_organization.fullname AS organiser,
          workshops_organization.domain AS organiser_domain,
          workshops_organization.country AS organiser_country_code,
          group_concat(workshops_tag.name) AS tags
   FROM workshops_event
   JOIN workshops_organization
   JOIN workshops_event_tags
   JOIN workshops_tag ON workshops_event.host_id = workshops_organization.id
   AND workshops_event.id = workshops_event_tags.event_id
   AND workshops_event_tags.tag_id = workshops_tag.id
   WHERE country_code = 'GB'
     OR organiser_country_code = 'GB'
   GROUP BY workshops_event.id
   ORDER BY date(workshops_event.start) DESC) AS workshops
LEFT JOIN
  (SELECT workshops_eventrequest.id AS event_request_id,
          workshops_eventrequest.event_id AS event_id,
          group_concat(workshops_knowledgedomain.name, ":") AS workshop_request_domains
   FROM workshops_eventrequest
   JOIN workshops_eventrequest_attendee_domains
   JOIN workshops_knowledgedomain ON workshops_eventrequest.id = workshops_eventrequest_attendee_domains.eventrequest_id
   AND workshops_eventrequest_attendee_domains.knowledgedomain_id = workshops_knowledgedomain.id
   GROUP BY workshops_eventrequest.id) AS workshop_requests ON workshops.id = workshop_requests.event_id;