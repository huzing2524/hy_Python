-- 报警事件记录信息
-- 设备上传真实数据如下：
--    {"AlarmType":"AlarmEvent",
--    "time":"2018-4-10 16:24:13",
--    "name":"01801d0fff000467-Name",
--    "content":"01801d0fff000467-Text",
--    "value":"1"}

create table if not exists hy_alarm_event (
	id serial primary key,
	device_id varchar,
	name varchar not null,
	content varchar not null,
	value varchar not null,
	time timestamp not null,
	create_time timestamp not null
);
-- 报警恢复事件记录信息
-- 设备上传真实数据如下
--    {"AlarmType":"AlarmRecover",
--    "time":"2018-4-10 16:24:4",
--    "name":"01801d0fff000467-Name",
--    "content":"01801d0fff000467-Text",
--    "value":"0"
--    }

create table if not exists hy_alarm_recover (
	id serial primary key,
	device_id varchar,
	name varchar not null,
	content varchar not null,
	value varchar not null,
	time timestamp not null,
	create_time timestamp not null
);

-- 设备上传的真实数据
CREATE TABLE hy_monitor_data (
	"time" timestamp NULL,
	device_id varchar NOT NULL,
	"name" varchar NOT NULL,
	value varchar NOT NULL
);

CREATE INDEX index_device_id ON hy_monitor_data USING btree (device_id);
CREATE INDEX index_device_id_time ON hy_monitor_data USING btree (device_id, "time");

